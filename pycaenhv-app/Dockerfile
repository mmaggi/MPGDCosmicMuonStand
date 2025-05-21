FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY CAENHVWrapper-6.6/ /opt/CAENHVWrapper-6.6/

# Change directory before executing install.sh
WORKDIR /opt/CAENHVWrapper-6.6

RUN apt-get update && \
    apt-get install -y wget && \
    wget https://snapshot.debian.org/archive/debian-security/20240504T151453Z/pool/updates/main/o/openssl/libssl1.1_1.1.1n-0+deb11u5_amd64.deb && \
    apt install -y ./libssl1.1_1.1.1n-0+deb11u5_amd64.deb && \
    rm ./libssl1.1_1.1.1n-0+deb11u5_amd64.deb
    
    
# Run the install script
RUN chmod +x /opt/CAENHVWrapper-6.6/install.sh && \
    /opt/CAENHVWrapper-6.6/install.sh && \
    ldconfig


# Set the library path just in case
ENV LD_LIBRARY_PATH=/usr/lib64:/usr/local/lib
    
COPY . .

CMD ["python3", "basic_test.py"]
