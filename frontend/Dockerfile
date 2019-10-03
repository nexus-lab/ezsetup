FROM node:8

LABEL vendor="NexusLab"
LABEL version="1.0.0"
LABEL description="EZSetup Front-end Service"

WORKDIR /var/www
COPY . /var/www

RUN npm install

EXPOSE 8080/tcp

CMD npm run dev
