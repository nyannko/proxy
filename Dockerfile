FROM sconecuratedimages/apps:python-2-alpine3.6
MAINTAINER nyannko

# HW mode not works for now
ENV SCONE_MODE=AUTO

# update alpine linux and install dependencies
RUN apk update && apk upgrade && \ 
    apk --no-cache add py-twisted gcc openssl-dev musl-dev linux-headers libffi-dev libsodium && \
    pip install --no-cache-dir incremental constantly && \
    pip install --no-cache-dir cryptography libnacl netifaces networkx datrie

# add source code to images
ADD . /opt/proxy

# switch working directory
WORKDIR /opt/proxy/socks5_udp

EXPOSE 40000

# for client proxy
CMD ["python","client.py"]

# for server proxy
#CMD ["python","client.py"] 

# build and run
# docker build -t bearapi/scone_docker_client .
# docker run -it -p 40000:40000 bearapi/scone_docker_client
