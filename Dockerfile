# syntax=docker/dockerfile:1
FROM python:3-alpine
WORKDIR /app
EXPOSE 8000
COPY . .
CMD ["./student-assessment.pyz"]
