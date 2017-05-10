FROM python:2

# Install necessary packages
RUN pip install buildbot requests

# Setup our image to live in the right place and run the right command
WORKDIR /app
CMD buildbot checkconfig master.cfg

# Copy in our code
COPY master /app/

# Mock up secret variables, etc..
COPY mock/* /app/
