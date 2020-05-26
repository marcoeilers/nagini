from collections import OrderedDict
from nagini_translation.models.converter import Converter, SNAP_TO, get_func_value, ScalaIterableWrapper


class Extractor:

    def translate_sort(self, jvm, s):
        terms = jvm.viper.silicon.state.terms
        def get_sort_object(name):
            return getattr(terms, 'sorts$' + name + '$')
        def get_sort_class(name):
            return getattr(terms, 'sorts$' + name)

        if isinstance(s, get_sort_class('Set')):
            return 'Set<{}>'.format(self.translate_sort(jvm, s.elementsSort()))
        elif isinstance(s, get_sort_object('Ref')):
            return '$Ref'
        elif isinstance(s, get_sort_class('Seq')):
            return 'Seq<{}>'.format(self.translate_sort(jvm, s.elementsSort()))
        else:
            return str(s)

    def try_evaluate(self, jvm, term, model):
        if isinstance(term, jvm.viper.silicon.state.terms.First):
            sub = self.try_evaluate(jvm, term.p(), model)
            if sub.startswith('($Snap.combine '):
                return self.get_parts(jvm, sub)[1]
        elif isinstance(term, jvm.viper.silicon.state.terms.Second):
            sub = self.try_evaluate(jvm, term.p(), model)
            if sub.startswith('($Snap.combine '):
                return self.get_parts(jvm, sub)[2]
        elif isinstance(term, jvm.viper.silicon.state.terms.Var):
            return model[term.id().name()]
        elif isinstance(term, jvm.viper.silicon.state.terms.SortWrapper):
            sub = self.try_evaluate(jvm, term.t(), model)
            sort_name = self.translate_sort(jvm, term.to())
            return get_func_value(model, SNAP_TO + sort_name, (sub,))
        raise Exception

    def get_parts(self, jvm, val):
        parser = getattr(getattr(jvm.viper.silver.verifier, 'ModelParser$'), 'MODULE$')
        res = []
        for part in ScalaIterableWrapper(parser.getApplication(val)):
            res.append(part)
        return res

    def extract_counterexample(self, jvm, pymethod, ce, modules):
        scala_store = ce.store()
        store = OrderedDict()
        for entry in ScalaIterableWrapper(scala_store):
            store[entry._1()] = entry._2()
        scala_model = ce.model()
        model = OrderedDict()
        for entry in ScalaIterableWrapper(scala_model.entries()):
            self.extract_model_entry(entry, jvm, model)

        heap = OrderedDict()
        for chunk in ScalaIterableWrapper(ce.heap()):
            self.extract_chunk(chunk, jvm, modules, model, heap)

        oheap = OrderedDict()
        if ce.oldHeap().isDefined():
            for chunk in ScalaIterableWrapper(ce.oldHeap().get()):
                self.extract_chunk(chunk, jvm, modules, model, oheap)

        converter = Converter(pymethod, model, store, heap, oheap, jvm, modules)
        return converter.generate_inputs()

    def extract_model_entry(self, entry, jvm, target):
        name = entry._1()
        value = entry._2()
        if isinstance(value, jvm.viper.silver.verifier.SingleEntry):
            target[name] = value.value()
        else:
            entry_val = OrderedDict()
            for option in ScalaIterableWrapper(value.options()):
                option_value = option._2()
                option_key = ()
                for option_key_entry in ScalaIterableWrapper(option._1()):
                    option_key += (option_key_entry,)
                entry_val[option_key] = option_value
            entry_val['else'] = value.els()
            target[name] = entry_val

    def extract_chunk(self, chunk, jvm, modules, model, target):
        if not isinstance(chunk, jvm.viper.silicon.state.BasicChunk):
            return
        resource_id = str(chunk.resourceID())
        if not resource_id in ('FieldID', 'PredicateID'):
            return
        if resource_id == 'FieldID':
            self.extract_field_chunk(chunk, jvm, modules, model, target)
        else:
            self.extract_predicate_chunk(chunk, modules, target)

    def extract_field_chunk(self, chunk, jvm, modules, model, target):
        field_name = str(chunk.id())
        recv_val = chunk.args().toIterator().next()
        value = self.try_evaluate(jvm, chunk.snap(), model)
        if field_name in ('list_acc', 'set_acc', 'dict_acc', 'dict_acc2'):
            # Special handling,
            pyfield = field_name
        else:
            pyfield = [f for mod in modules for c in mod.classes.values() for f in c.fields.values()
                       if f.sil_name == field_name][0]

        target[(recv_val, pyfield)] = ' '.join(value.split())

    def extract_predicate_chunk(self, chunk, modules, target):
        pred_name = str(chunk.id())
        pypreds = [p for mod in modules for p in mod.predicates.values()
                   if p.sil_name == pred_name]
        if not pypreds:
            pypreds = [p for mod in modules for c in mod.classes.values() for p in c.predicates.values()
                       if p.sil_name == pred_name]
        pypred = pypreds[0]
        pred_args = []
        for pred_arg in ScalaIterableWrapper(chunk.args()):
            pred_args.append(pred_arg)

        target[(tuple(pred_args), pypred)] = None