import time
import docker
import socket


def make_container(options, max_attempts=10):
    client = docker.from_env()
    _container = client.containers.run(**options)
    attempt = 0
    while _container.status != "running":
        _container = client.containers.get(_container.name)
        if _container.status == "running":
            return _container
        attempt += 1
        if attempt >= max_attempts:
            break
        time.sleep(1)
    return False


def wait_for_container_output(container_id, output, wait_seconds=30):
    client = docker.from_env()
    container = client.containers.get(container_id)
    attempt = 0
    while True:
        logs = container.logs()
        if output in logs.decode():
            return True
        attempt += 1
        if attempt >= wait_seconds:
            break
        time.sleep(1)
    return False


def remove_container(container_id, max_attempts=10):
    client = docker.from_env()
    container = client.containers.get(container_id)
    container.stop()
    container.wait()
    container.remove()
    attempt = 0
    while True:
        try:
            client.containers.get(container_id)
            attempt += 1
            if attempt >= max_attempts:
                break
            time.sleep(1)
        except docker.errors.NotFound:
            return True
    return False


def check_port(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex((host, port))
            return result == 0
    except socket.error:
        return False
    return False
