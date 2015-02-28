A toy implementation of an "encrypted" chat client that uses RSA in a sort of ECB mode.
The usual way of implementing RSA is to only use RSA to exchange keys and then use symmetric
encryption for further communication. I didn't feel like doing that. 

This implementation is not actually secure in any conceivable way. eve.py will be populated
with attacks in the future and I'll slowly be improving the security of the implementation
for funsies. 

Instructions
1. open console change to this directory
2. run "python client.py" and then say hi to everyone :)
