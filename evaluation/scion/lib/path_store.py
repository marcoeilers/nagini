# Copyright 2014 ETH Zurich
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
:mod:`path_store` --- Path record storage and selection for path servers
========================================================================
"""
# Stdlib
import logging

# External
import yaml

# SCION
from lib.packet.pcb import PathSegment
from lib.packet.scion_addr import ISD_AS
from lib.util import SCIONTime, load_yaml_file
from typing import cast, Dict, List, Optional, Tuple
from nagini_contracts.contracts import *


class PathPolicy(object):
    """Stores a path policy."""
    def __init__(self) -> None:  # pragma: no cover
        Ensures(self.State())
        self.best_set_size = 5
        self.candidates_set_size = 20
        self.history_limit = 0
        self.update_after_number = 0
        self.update_after_time = 0
        self.unwanted_ases = []  # type: List[ISD_AS]
        self.property_ranges = {}  # type: Dict[str, Tuple[int, int]]
        self.property_weights = {}  # type: Dict[str, int]
        Fold(self.State())

    @Predicate
    def State(self) -> bool:
        return (Acc(self.best_set_size) and
                Acc(self.candidates_set_size) and
                Acc(self.history_limit) and
                Acc(self.update_after_number) and
                Acc(self.update_after_time) and
                Acc(self.unwanted_ases) and Acc(list_pred(self.unwanted_ases)) and
                Acc(self.property_ranges) and Acc(dict_pred(self.property_ranges)) and
                Acc(self.property_weights)) and Acc(dict_pred(self.property_weights))

    def get_path_policy_dict(self) -> Dict[str, object]:  # pragma: no cover
        Requires(Acc(self.State(), 1/100))
        Ensures(Acc(self.State(), 1/100))
        Ensures(Acc(dict_pred(Result())))
        Ensures('best_set_size' in Result())
        """Return path policy info in a dictionary."""
        Unfold(Acc(self.State(), 1/100))
        result = {
            'best_set_size': self.best_set_size,
            'candidates_set_size': self.candidates_set_size,
            'history_limit': self.history_limit,
            'update_after_number': self.update_after_number,
            'update_after_time': self.update_after_time,
            'unwanted_ases': self.unwanted_ases,
            'property_ranges': self.property_ranges,
            'property_weights': self.property_weights
        }
        Fold(Acc(self.State(), 1/100))
        return result

    def check_filters(self, pcb: PathSegment) -> bool:
        Requires(Acc(pcb.State(), 1/10))
        Requires(Acc(self.State(), 1 / 7))
        Requires(self.valid_ranges())
        Ensures(Acc(pcb.State(), 1 / 10))
        Ensures(Acc(self.State(), 1 / 7))
        """
        Runs some checks, including: unwanted ASes and min/max property values.

        :param pcb: beacon to analyze.
        :type pcb: :class:`PathSegment`
        :returns:
            True if any unwanted AS is present or a range is not respected.
        :rtype: bool
        """
        assert isinstance(pcb, PathSegment)
        isd_as = self._check_unwanted_ases(pcb)
        if isd_as:
            logging.warning("PathStore: pcb discarded, unwanted AS(%s): %s",
                            isd_as, pcb.short_desc())
            return False
        reasons = self._check_property_ranges(pcb)
        if reasons:
            logging.info("PathStore: pcb discarded(%s): %s",
                         ", ".join(reasons), pcb.short_desc())
            return False
        ia = self._check_remote_ifid(pcb)
        if ia:
            logging.error("PathStore: pcb discarded, remote IFID of %s unknown",

                          )
            return False
        return True

    def _check_unwanted_ases(self, pcb: PathSegment) -> Optional[ISD_AS]:  # pragma: no cover
        Requires(Acc(pcb.State(), 1/20))
        Requires(Acc(self.State(), 1/8))
        Ensures(Acc(pcb.State(), 1 / 20))
        Ensures(Acc(self.State(), 1 / 8))
        """
        Checks whether any of the ASes in the path belong to the black list.

        :param pcb: beacon to analyze.
        :type pcb: :class:`PathSegment`
        """
        asms = pcb.iter_asms()
        for asm in asms:
            Invariant(Forall(asms, lambda a: (Acc(a.State(), 1 / 4), [])))
            Invariant(Acc(self.State(), 1/9))
            Invariant(Acc(pcb.State(), 1 / 20))
            isd_as = asm.isd_as()
            Unfold(Acc(self.State(), 1/10))
            if isd_as in self.unwanted_ases:
                Fold(Acc(self.State(), 1 / 10))
                return isd_as
            Fold(Acc(self.State(), 1 / 10))

    def _check_range(self, reasons: List[str], name: str, actual: int) -> None:
        Requires(Acc(list_pred(reasons)))
        Requires(Acc(self.State(), 1/200))
        Requires(Unfolding(Acc(self.State(), 1/400), name in self.property_ranges))
        Ensures(Acc(list_pred(reasons)))
        Ensures(Acc(self.State(), 1 / 200))

        range_ = Unfolding(Acc(self.State(), 1/300), self.property_ranges[name])
        if not range_:
            return
        if (actual < range_[0] or actual > range_[1]):
            reasons.append("%s: %d <= %d <= %d" % (
                name, range_[0], actual, range_[1]))

    def _check_property_ranges(self, pcb: PathSegment) -> List[str]:
        Requires(Acc(self.State(), 1 / 100))
        Requires(self.valid_ranges())
        Ensures(Acc(self.State(), 1 / 100))
        Ensures(Acc(list_pred(Result())))
        """
        Checks whether any of the path properties has a value outside the
        predefined min-max range.

        :param pcb: beacon to analyze.
        :type pcb: :class:`PathSegment`
        """

        reasons = []  # type: List[str]
        self._check_range(reasons, "PeerLinks", pcb.get_n_peer_links())
        self._check_range(reasons, "HopsLength", pcb.get_n_hops())
        self._check_range(reasons, "DelayTime",
                          int(SCIONTime.get_time()) - pcb.get_timestamp())
        self._check_range(reasons, "GuaranteedBandwidth", 10)
        self._check_range(reasons, "AvailableBandwidth", 10)
        self._check_range(reasons, "TotalBandwidth", 10)
        return reasons

    def _check_remote_ifid(self, pcb: PathSegment) -> Optional[ISD_AS]:
        Requires(Acc(pcb.State(), 1 / 20))
        Ensures(Acc(pcb.State(), 1 / 20))
        """
        Checkes whether any PCB markings have unset remote IFID values for
        up/downstream ASes. This can happen during normal startup depending
        on the timing of PCB propagation vs IFID keep-alives, but should
        not happen once the infrastructure is settled.
        Remote IFID is only allowed to be 0 if the corresponding ISD-AS is
        0-0.
        """
        asms = pcb.iter_asms()
        for asm in asms:
            Invariant(Forall(asms, lambda a: (Acc(a.State(), 1 / 4), [])))
            pcbms = asm.iter_pcbms()
            for pcbm in pcbms:
                Invariant(Forall(pcbms, lambda p: (Acc(p.State(), 1 / 4), [])))
                if (pcbm.inIA().to_int() and
                        not Unfolding(Acc(pcbm.State(), 1/8),
                                      Unfolding(Acc(pcbm.p.State(), 1/16), pcbm.p.inIF))):
                    return pcbm.inIA()
                if (pcbm.outIA().to_int() and
                        not Unfolding(Acc(pcbm.State(), 1/8),
                                      Unfolding(Acc(pcbm.p.State(), 1/16), pcbm.p.outIF))):
                    return pcbm.outIA()
        return None

    @classmethod
    def from_file(cls, policy_file: str) -> 'PathPolicy':  # pragma: no cover
        """
        Create a PathPolicy instance from the file.

        :param str policy_file: path to the path policy file
        """
        policy_dict = load_yaml_file(policy_file)
        # Fails, because the validity of the loaded dict is not guaranteed.
        return cls.from_dict(policy_dict)

    @classmethod
    def from_dict(cls, policy_dict: Dict[str, object]) -> 'PathPolicy':  # pragma: no cover
        Requires(Acc(dict_pred(policy_dict), 1/10))
        Requires(valid_policy(policy_dict))
        Requires(Acc(dict_pred(policy_dict['PropertyRanges'])))
        Requires(Acc(dict_pred(policy_dict['PropertyWeights'])))
        Ensures(Acc(dict_pred(policy_dict), 1 / 10))
        """
        Create a PathPolicy instance from the dictionary.

        :param dict policy_dict: dictionary representation of path policy
        """
        path_policy = cls()
        path_policy.parse_dict(policy_dict)
        return path_policy

    def parse_dict(self, path_policy: Dict[str, object]) -> None:
        Requires(self.State())
        Requires(Acc(dict_pred(path_policy), 1/20))
        Requires(valid_policy(path_policy))
        Requires(Acc(dict_pred(path_policy['PropertyRanges'])))
        Requires(Acc(dict_pred(path_policy['PropertyWeights'])))
        Ensures(self.State())
        Ensures(Acc(dict_pred(path_policy), 1 / 20))
        """
        Parses the policies from the dictionary.

        :param dict path_policy: path policy.
        """
        Unfold(self.State())
        self.best_set_size = cast(int, path_policy['BestSetSize'])
        self.candidates_set_size = cast(int, path_policy['CandidatesSetSize'])
        self.history_limit = cast(int, path_policy['HistoryLimit'])
        self.update_after_number = cast(int, path_policy['UpdateAfterNumber'])
        self.update_after_time = cast(int, path_policy['UpdateAfterTime'])
        unwanted_ases = cast(str, path_policy['UnwantedASes']).split(',')
        for unwanted in unwanted_ases:
            Invariant(Acc(self.unwanted_ases, 1/2) and Acc(list_pred(self.unwanted_ases)))
            self.unwanted_ases.append(ISD_AS(unwanted))
        property_ranges = cast(Dict[str, str], path_policy['PropertyRanges'])
        for key in property_ranges:
            Invariant(Acc(self.property_ranges, 1/2) and Acc(dict_pred(self.property_ranges)))
            property_range = property_ranges[key].split('-')
            property_range_temp = int(property_range[0]), int(property_range[1])
            self.property_ranges[key] = property_range_temp
        self.property_weights = cast(Dict[str, int], path_policy['PropertyWeights'])
        Fold(self.State())

    @Pure
    def valid_ranges(self) -> bool:
        Requires(Acc(self.State(), 1/200))
        return Unfolding(Acc(self.State(), 1/200),
                         'PeerLinks' in self.property_ranges and
                         'HopsLength' in self.property_ranges and
                         'DelayTime' in self.property_ranges and
                         'GuaranteedBandwidth' in self.property_ranges and
                         'AvailableBandwidth' in self.property_ranges and
                         'TotalBandwidth' in self.property_ranges
                         )

    def to_str(self) -> str:  # Renamed to avoid incompatible override of object.__str__
        Requires(Acc(self.State(), 1/10))
        Ensures(Acc(self.State(), 1 / 10))
        path_policy_dict = self.get_path_policy_dict()
        path_policy_str = yaml.dump(path_policy_dict)
        return path_policy_str

DICT_STR_STR = Dict[str, str]
DICT_STR_INT = Dict[str, int]


@Pure
def valid_policy(path_policy: Dict[str, object]) -> bool:
    Requires(Acc(dict_pred(path_policy), 1 / 1000))
    return ('BestSetSize' in path_policy and
            'CandidatesSetSize' in path_policy and
            'HistoryLimit' in path_policy and
            'UpdateAfterNumber' in path_policy and
            'UpdateAfterTime' in path_policy and
            'UnwantedASes' in path_policy and
            'PropertyRanges' in path_policy and
            'PropertyWeights' in path_policy and
            isinstance(path_policy['BestSetSize'], int) and
            isinstance(path_policy['CandidatesSetSize'], int) and
            isinstance(path_policy['HistoryLimit'], int) and
            isinstance(path_policy['UpdateAfterNumber'], int) and
            isinstance(path_policy['UpdateAfterTime'], int) and
            isinstance(path_policy['UnwantedASes'], str) and
            isinstance(path_policy['PropertyRanges'], DICT_STR_STR) and
            isinstance(path_policy['PropertyWeights'], DICT_STR_INT))


