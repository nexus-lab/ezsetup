FROM python:3.6

LABEL vendor="NexusLab"
LABEL version="1.0.0"
LABEL description="EZSetup API Service"

WORKDIR /var/www
COPY . /var/www

RUN pip install pipenv
RUN pipenv install --system --deploy

EXPOSE 5000/tcp

CMD python create_root.py && python app.py
