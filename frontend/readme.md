docker build -t frontend:0.1 ./frontend
docker run --rm -p 8080:80 --name frontend frontend:0.1
http://localhost:8080
