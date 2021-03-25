Описание
========
Web-приложение для просмотра в реальном времени активности телефонных номеров Asterisk'а.

Скриншот интерфейса
===================
![Screenshot](http://blog.kgd.in/wp-content/uploads/2016/01/2016-01-25-08-42-21-Активность-звонков-v.2-—-Opera_censored.jpg)

Способ установки
================
1. Склонировать репозиторий
2. Поместить содержимое папки web в директорию на Web-Сервере
Настройки
=========
1. Отредактировать файл **daemon/config.py**:
```Python
config = {'host': '192.168.50.250',	# IP-адрес AMI Asterisk
          'port': 5038,			# Порт AMI Asterisk
          'login': 'nikolay',		# Логин AMI Asterisk
          'secret': 'qwerty'}		# Пароль AMI Asterisk
```
2. Отредактировать файл **daemon/wraps_config.py**:
```Python
config = {'ws_port': 8888}		# Порт WebSocket-сервера
```
Остальные строки данного конфигурационного файла предназначены для примера обработки событий поступающих с AMI Asterisk'а.
3. В файле **daemon/py-ami.py** в функцию wrap_list добавлять свои обработки событий. Примеры:
```Python
self.ami.wrapper({'PeerStatus': {'function': self.wraps.peer_status}})
```
или
```Python
self.ami.wrapper({'PeerStatus': {'function': self.wraps.peer_status,
                                 'filter': {'PeerStatus': 'Registered'}}})
```
где 'PeerStatus' - это событие из AMI Asterisk'а  
function - указывает на функцию, которая будет обрабатывать данное событие, в функцию передается в виде массива дополнительные данные по данному событию  
filter - дополнительный фильтр по данному событию

Также есть возможность отменять обработку событий. Пример удаления всех событий с данным названием:
```Python
self.ami.unwrapper('Dial')
```
Пример удаления всех событий с дополнительным фильтром:
```Python
self.ami.unwrapper({'Dial': {'filter': {'SubEvent': 'End'}}})
```
4. Запустить AMI-демона командой **daemon/py-ami.py start** . Параметры командной строки демона:
  - start - Запуск демона
  - stop - Остановка демона
  - restart - Перезапуск демона
5. Файл **index.html** в скопированной папке на Web-Сервер отредактировать, указав IP-адрес и порт WebSocket-сервера:
```JavaScript
var ws_ip = "192.168.0.7";
var ws_port = "8888";
```
Зависимости
===========
- Python > 2.5 & < 3

По всем вопросам обращаться ко мне в блоге: http://blog.kgd.in