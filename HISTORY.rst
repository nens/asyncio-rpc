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
