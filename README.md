# Игра мафия
Данный репозиторий реализует клиент и сервер для игры в мафию на основе `gRPC`.
Реализован сервер игрового чата на основе `RabbitMQ`.
Реализован `REST` сервер, сбор игровой статистики и общая регистрация на основе `JWT`.
Реализован `GraphQL` сервер и клиент, которые позволяют получаться информацию об играх.

## Сборка
Сервер игры, сервер чата, rest сервер и клиент собираются командой:
```
docker compose build --no-cache
```
Адрес игрового сервера (`SERVER_ADDR`) передается через файл `.env`, который находится в корне репозитория.
Адрес по умолчанию `0.0.0.0:50051`.
Сервер игры подключает игроков и создает новую сессию сразу, как только набирается 4 свободных игрока.
Общение игроков происходит через сервер чата.

## Запуск
Сначала запускайте сервер `RabbitMQ`, 
затем сервер игры, 
затем сервер игрового чата, 
затем `REST` сервер, 
затем `GraphQL` сервер 
и только потом клиенты игры или клиент `GraphQL`.

Запустить сервер `RabbitMQ`:
```
docker compose up rabbitmq
```
Запустить сервер игры:
```
docker compose up game_server
```
Запустить сервер игрового чата:
```
docker compose up chat_server
```
Запустить `REST` сервер:
```
docker compose up rest_server
```
Запустить `GraphQL` сервер:
```
docker compose up graphql_server
```
Запустить `GraphQL` клиент:
```
docker compose run graphql_client
```
Запустить клиент (можно выполнять несколько раз, для создания множества клиентов):
```
docker compose run client
```

## GraphQL Сервер
`GraphQL` сервер работает на порту `50021`, для взаимодействия с ним используется `GraphQL` клиент.
Клиент дает возможность получения списка текущих и прошлых игр, просмотра Scoreboard конкретной игры, 
а также добавление комментариев к играм. Открытый Scoreboard обновляется в соответствии с изменениями игровой ситуации до тех пор, 
пока игра не закончится.

Команды клиента:
```
c - Получить список текущих игр.
p - Получить список прошедших игр.
s - Получить Scoreboard (не обновляетя).
ss - Получить обновляющийся Scoreboard.
a - Добавить коменнатрий к игре.
exit - Выйти из клиента.
```

Команды `s`, `ss` и `a` дополнительно запросят идентификатор сессии, над которой совершается операция.
Команда `a` дополнительно запросит добавляемый комментарий, и вернет список текущих комментариев к игре.
Если запустить команду `ss` для сессии, которой еще нет, но до нее скору дойдут (боты играют на сервере),
то сначала вместо Scoreboard будет отображаться строка `Sid value is invalid`, а когда сессия создастся, появится сам Scoreboard.

## REST Сервер

В качестве клиента взаимодействия с `REST` сервером используется `curl`.
`REST` сервер работает на порту `50031`.
Далее показаны примеры запросов и методов `REST` сервера.

#### Зарегистрировать пользователя:
Для регистрации требуется указать `pid` игрока. `pid` выдается игровым сервером при подключении клиента (строка "`Player successfully registered on server with id <PID>`") и пароль, 
который будет использоваться данным `pid`:
```
curl -X POST -H "Content-Type: application/json" -d '{"pid": 23, "pwd": "1234"}' http://localhost:50031/register
```

#### Получить JWT токен:
Если игрок зарегистрирован, можно получить его `JWT` токен. `JWT` токен требуется в модифицирующих запросах 
`PUT` и `DELETE` (подставляется вместо `<JWT_TOKEN>`). Для получения токена требуется указать `pid` и пароль:

```
curl -X POST -H "Content-Type: application/json" -d '{"pid":23, "pwd": "1234"}' http://localhost:50031/login
```

#### Информация об игроке:
Получить информацию об игроках (указываются их `pid`):
```
curl -X GET -H "Content-Type: application/json" -d '{"pids":[0, 1, 23]}' http://localhost:50031/player
```

Обновить информацию игрока (указываются обновляемые поля и их новые значения).
Поля, доступные для обновления: `name`, `email`, `male`.
```
curl -X PUT -H "Authorization: Bearer <JWT_TOKEN>" -H "Content-Type: application/json" -d '{"name":"Ivan", "email":"ivan@mail.com", "gender":"male"}' http://localhost:50031/player    
```

Для обновления аватарки вместо `<PATH_TO_AVATAR>` подставьте путь к файлу аватарки (например локальный файл `my_avatar.jpg`).
Файл должен быть формата `.jpg`:
```
curl -X PUT -H "Authorization: Bearer <JWT_TOKEN>" -F avatar=@<PATH_TO_AVATAR> http://localhost:50031/player
```

Для удаления информации по игроку требуется указать удаляемые поля.
Доступные поля: `name`, `email`, `gender`, `avatar`.
```
curl -X DELETE -H "Authorization: Bearer <JWT_TOKEN>" -H "Content-Type: application/json" -d '{"values":["name", "email", "gender", "avatar"]}' http://localhost:50031/player
```

#### Получить ссылку на PDF:
Прежде чем получить сам PDF, нужно асинхронным запросом получить ссылку на файл, 
где вместо `<PID>` указывается `pid` игрока:
```
curl -X GET http://localhost:50031/stats/<PID>
```

#### Получить PDF файл:
Получить сам PDF (вместо `<PID>` указывается `pid` игрока) и сохранить его в `temp.pdf`:
```
curl -X GET http://localhost:50031/pdf/<PID> >temp.pdf
```

## Игровой процесс
На старте клиент спросит, хотите ли вы запустить его в бот режиме.
В режиме бота клиент полностью автономен, каждый раз выбирает случайные действия.
Далее будет запрошено имя, под которым данный клиент будет отображаться на сервере.
Имена могут быть не уникальными, ведь сервер выдает каждому клиенту уникальный идентификатор.
После подключения к серверу, клиент будет ожидать от вас ввода команд.
Всегда можно ввести команду `help` и увидеть список доступных команд.
Кроме `help` есть команды:
```
c - Переподключиться к серверу с другим именем (текущая сессия теряется).
v - Узнать доступные действия во время активной сессии игры в мафию (их также можно вводить).
a - Узнать список всех игроков на сервере.
s - Узнать состояние текущей сессии (полезная и очень информативная команда).
t <TEXT> - Отправить сообщение в чат. Например 't Hello!' отправит сообщение 'Hello!'.
exit - Выйти из клиента.
```

Если запустили клиент в бот режиме, не бойтесь убивать его, ведь сам он играть не закончит.
Сервер распознает такие ситуации и примет соответствующие действия.
Если отключаемый игрок имел статус духа, до текущая сессия не завершается, 
если же игрок не был духом, сессия завершается для всех.
Голосовать за себя можно.
Если в процессе голосования нельзя установить одного лидера, тогда никто не умирает.
Общение в игре идет через сервер чата. Пока клиент не находится в сессии, его сообщения 
адресуются таким же бессессионным игрокам. Как только клиент подключается к сессии, его 
общение начинает происходить внутри сессии согласно правилам (днем общаются все, ночью только мафия).
Духи могут читать сообщения, но не могут писать.

Приятной игры!
