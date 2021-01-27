FROM ubuntu:20.04

RUN apt-get update -y && \
    apt-get install -y python3.8 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    python3-pip \
    cmake \
    python3-dev \
    build-essential
    
RUN pip3 install --upgrade pip

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT [ "python3" ]

CMD [ "app.py" ]