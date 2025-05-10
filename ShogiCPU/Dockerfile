FROM public.ecr.aws/lambda/python:3.13

RUN dnf install -y gcc gcc-c++ make

WORKDIR /var/task
COPY Engine Engine
COPY YaneuraOu YaneuraOu
WORKDIR /var/task/YaneuraOu/source
RUN make &&\
  mv YaneuraOu-by-gcc /var/task/Engine/
COPY app.py ${LAMBDA_TASK_ROOT}
CMD [ "app.handler" ]
