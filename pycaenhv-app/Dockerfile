FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY CAENHVWrapper-6.6/ /opt/CAENHVWrapper-6.6/

# Change directory before executing install.sh
WORKDIR /opt/CAENHVWrapper-6.6

# Run the install script
RUN chmod +x /opt/CAENHVWrapper-6.6/install.sh && \
    /opt/CAENHVWrapper-6.6/install.sh && \
    ldconfig

# Set the library path just in case
ENV LD_LIBRARY_PATH=/usr/local/lib
    
COPY . .

CMD ["python3", "basic_test.py"]
