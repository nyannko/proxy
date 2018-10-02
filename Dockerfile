# for client proxy
FROM sconecuratedimages/apps:python-2-alpine3.6 
MAINTAINER nyannko

# run sgx enclaves when available
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

ENV SCONE_ALPINE=1
ENV SCONE_VERSION=1

EXPOSE 40000

CMD ["python","client.py"] 

# for server proxy
# CMD ["python","server.py"] 

# client: build and run 
# docker build -t bearapi/scone_docker_client .
# docker run -it -p 40000:40000 bearapi/scone_docker_client

# client: run with sgx 
# docker run -it -p 40000:40000 -v $PWD:/opt/proxy -w /opt/proxy/socks5_udp --device=/dev/isgx -it scone
