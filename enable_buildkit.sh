#!/bin/bash

# Создаем файл конфигурации Docker для включения BuildKit
mkdir -p ~/.docker
echo '{
  "features": {
    "buildkit": true
  }
}' > ~/.docker/config.json

# Добавляем переменные окружения для использования BuildKit
echo 'export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1' >> ~/.bashrc

echo "BuildKit настроен для ускорения сборки Docker."
echo "Пожалуйста, перезапустите терминал или выполните: source ~/.bashrc"