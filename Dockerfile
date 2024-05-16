# set the kernel to use
FROM python:3
# copy the requirements file
COPY requirements.txt requirements.txt
# install the needed requirements
RUN pip3 install -r requirements.txt
# copy all the files in the container
COPY . .
# the command that will be executed when the container will start
CMD ["python3","./bot.py"]