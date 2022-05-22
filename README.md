## how to build
 ```
docker build -t booking .
 ```

## how to run
 ```
docker run -i -t \
    -e BOOK_DATE='YYYY-MM-DD' \
    -e BOOK_TIME='HH,HH' \
    -e COURT_NUMBER='10' \
    -e MEMBER_INFORMATION='' \
    -v "$PWD":/app  \
    --name booking_container booking
 ```

 ```
   docker run -i -t -d --rm\
     -e BOOK_DATE='YYYY-MM-DD' \
    -e BOOK_TIME='HH,HH' \
    -e COURT_NUMBER='10' \
    -e MEMBER_INFORMATION='' \
    --name booking_container booking \
    python3 book.py
 ```