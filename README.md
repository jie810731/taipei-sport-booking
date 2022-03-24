## how to build
 ```
docker build -t booking .
 ```

## how to run
 ```
docker run -i -t \
    -e BOOK_DATE='YYYY-MM-DD' \
    -e BOOK_TIME='HH,HH' \
    -e COURT='736' \
    --env-file .env \
    -v "$PWD":/app  \
    --name booking_container booking
 ```