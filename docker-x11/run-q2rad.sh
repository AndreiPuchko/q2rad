docker build -t q2rad .

mkdir -p q2rad_storage/Desktop
chmod -R 777 q2rad_storage

docker run -it \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $(pwd)/q2rad_storage:/home/q2rad \
    -e DISPLAY=$DISPLAY \
    -u q2rad \
    q2rad \
    python3 -m q2rad
