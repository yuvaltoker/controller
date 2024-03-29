# What image do we start from
FROM ubuntu:latest

###################################
#      rabbitmq dependencies      #
###################################
# install python dependencies
RUN apt update && apt upgrade -y
RUN apt install -y python curl
RUN curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py && python get-pip.py
RUN python -m pip install pika --upgrade
RUN pip install --upgrade pip enum34
# for multiproccessing-
RUN pip install mpire

##################################
#      mongodb dependencies      #
##################################
# install python dependencies

RUN python -m pip install pymongo pandas
# if an error accurs check last comment on https://stackoverflow.com/questions/52857945/python2-installing-json-util

#####################################
#      controller dependencies      #
#####################################
# install wait package
RUN python -m pip install waiting

##################################################
#      waiting for other containers service      #
##################################################
## Add the wait script to the image
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.9.0/wait /wait
RUN chmod +x /wait

RUN mkdir /controller-scripts

## Add your application to the docker image (comment out in case of working with volume)
#ADD ./controller.py .
#RUN chmod +x controller.py


## Launch the wait tool and then your application
#CMD /wait && ./controller.py
