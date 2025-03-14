# Running NetAnim from remote station

On host station running ns-3 simulator, you can run an
[xpra](https://github.com/Xpra-org/xpra) session.

```bash
$ xpra start :10 --start-child=./ns-allinone-3.39/netanim-3.109/NetAnim --bind-tcp=0.0.0.0:10000 --exit-with-children
```

On client, just attach to the newly created server socket.

```bash
$ xpra attach tcp:<server_address>:10000
```
