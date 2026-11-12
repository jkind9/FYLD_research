# Basalt (BSD-3) from its published Ubuntu 22.04 binary release; installs into /root/.local.
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl tar xz-utils libgl1 libglu1-mesa \
    libtbb12 libfmt8 && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://gitlab.com/VladyslavUsenko/basalt/-/raw/master/scripts/install.sh | sh
ENV PATH=/root/.local/bin:$PATH
ENV LD_LIBRARY_PATH=/root/.local/lib
