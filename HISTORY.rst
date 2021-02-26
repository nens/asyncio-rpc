0.1.10 (2021-02-26)
-------------------

- Disabled logging errors for missing Asyncio futures 
  for subscriptions.


0.1.9 (2021-02-22)
------------------

- Bugfix: asyncio future that waits for return RPC message needs
  to be created before sending RPC message to RPC server.

- Added debug logging statements.

0.1.8 (2021-02-05)
------------------

- Add numpy int32 and int64 serializer.


0.1.7 (2020-01-10)
------------------

- When a message from the client has not been received by 
  a server it raises a NotReceived exception instead of
  an assert error.


0.1.6 (2019-12-30)
------------------

- Added pub/sub support to allow sending continuous updates
  from the server for a client subscription

- Add slice serialization/deserialization support


0.1.5 (2019-12-23)
------------------

- Server.serve() methode respawns on internal tasks errors

- Better error handling in server.


0.1.4 (2019-10-03)
------------------

- Client now raises RPCTimeoutError if the result of a RPC call took to long to
  be received.

- Client.serve() method respawns internal tasks on errors.


0.1.3 (2019-08-21)
------------------

- Verbose feedback on assertion error while trying to unpack dataclasses.


0.1.2 (2019-07-04)
------------------

- Fixed bug with bytes/str serialization/deserialization


0.1.1 (2019-04-29)
------------------

- Added channel override option in client.rpc_call


0.1.0 (2019-03-20)
------------------

- first pypi release
