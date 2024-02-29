FROM python:3.8.18

# add dotnet repo
RUN wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
RUN dpkg -i packages-microsoft-prod.deb
RUN rm packages-microsoft-prod.deb
RUN apt update

# install dotnet and boogie (needed for carbon verifier)
RUN apt install -y dotnet-sdk-6.0
RUN dotnet tool install --global Boogie --version 2.15.9
ENV BOOGIE_EXE=/root/.dotnet/tools/boogie

# install openjdk 21 and all required nagini python packages
RUN apt install -y msopenjdk-21
COPY ./requirements.txt ./
RUN pip install -r ./requirements.txt

# copy over and install nagini source code
WORKDIR /installation
COPY src ./src
COPY setup.py README.rst ./
RUN pip install .
COPY tests ./tests

# some tests (such as tests/io/verification/test_forall_exists.py) require "from resources.library import ..."
# set MYPYPATH to find that package
ENV MYPYPATH=/installation/tests/io/verification:$MYPYPATH

# don't generate __pycache__
ENV PYTHONDONTWRITEBYTECODE=1

COPY entrypoint.sh ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]

#RUN nagini --verifier silicon --write-viper-to-file iap_bst.vpr tests/functional/verification/examples/iap_bst.py
#RUN nagini --verifier carbon  --write-viper-to-file iap_bst.vpr tests/functional/verification/examples/iap_bst.py