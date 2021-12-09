# What image do we start from
FROM ubuntu:latest

###################################
#      rabbitmq dependencies      #
###################################
# install python dependencies
RUN apt update && apt upgrade -y
RUN apt install -y python 
RUN curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py && python get-pip.py
RUN python -m pip install pika --upgrade
RUN pip install --upgrade pip enum34

##################################################
#      waiting for other containers service      #
##################################################
## Add the wait script to the image
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.9.0/wait /wait
RUN chmod +x /wait

## Add your application to the docker image (commented in case of working with volume)
ADD ./controller.py .
RUN chmod +x controller.py


## Launch the wait tool and then your application
CMD /wait && ./controller.py
