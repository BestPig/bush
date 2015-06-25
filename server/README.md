
## get started

```sh
cd server
php -S 127.0.0.1:8080
```

## requirements

 - `php5` (5.3 for normal use, but 5.4 is required to use PHP built-in server as is shown in the get started)
 - `php5-sqlite`

## authentication & tips

#### By default all files are public.

Please don't use `php -S` for production, the built-in server must be used for developments / tests only ([php-doc-webserver](https://php.net/manual/features.commandline.webserver.php)).

Use apache, nginx or any other web servers.

It is __strongly reccomended__ that you add a Basic Authentication on the bush root directory.
The client supports this and it is the only option if you don't want to share all your files publicly.
