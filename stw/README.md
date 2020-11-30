# da

Requirements:
- Use recent stable version of Hyperledger Sawtooth (1.2.4 currently)
- Setup network having 1 validator and 2 clients
- Develop CLI client
- Only one client (first) should have manager role
- A client should be able to issue new token
- Each account has own private/public keys and name like 'X12345'
- Any account can transfer an asset to another account
- Any account has secure access to his balance with their public key
- Manager can access any balance