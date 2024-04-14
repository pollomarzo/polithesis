FROM nest/nest-simulator:3.6

# not sure if "volumes" in compose runs before or after this, so i'll just copy it
COPY ./requirements.txt .
# --quiet
RUN pip install -r requirements.txt
