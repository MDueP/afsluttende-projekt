# afsluttende-projekt


## Nginx Config:

    server {
    if ($host = www.mduep.dk) {
        return 301 https://$host$request_uri;
    } 


    if ($host = mduep.dk) {
        return 301 https://$host$request_uri;
    } 


    listen 80;
    server_name mduep.dk www.mduep.dk;
    return 301 https://$host$request_uri;
    } 

    server {
        listen 443 ssl;
        server_name mduep.dk www.mduep.dk;
        ssl_certificate /etc/letsencrypt/live/mduep.dk/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/mduep.dk/privkey.pem; 


        location / {
            proxy_pass http://localhost:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
        }
    }
