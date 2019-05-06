Quickstart
==========

We showed you sample MSM client (master) usage at the :ref:`main page <index-sample-label>`. However, to run such code
properly, you first need a working modbus server (slave) at your *localhost*. Because of that, we will first create
a sample modbus server with some neet memory mapping. Next, we will create a client talking to the server.

The code below will:
 - allocate 16 bytes of memory
 - define some variables on this memory
 - start modbus TCP server worker
 - present those variables in cli

.. _modbus-server-example:

ex_server_mapper.py

.. literalinclude:: ../../../examples/ex_server_mapper.py
    

Whole advantage of using MSM as your modbus backend comes from two things:
 - You are not using modbus functions directly, instead you use *memory variables* like ordinary python variables
 - You dont bother yourself with serving modbus server/client by yourself, instead, you just instantiating it and tells it to *run*

Server code will pretty print declared *memory variables* to show its content. Especially it will show changes while you 
will be altering them as a client, and it will periodically alter **ERROR_STATE** variable to show you that you can see this changes from
the client side. Lets now write some code for the client:

.. _modbus-client-example:

ex_client_mapper.py

.. literalinclude:: ../../../examples/ex_client_mapper.py
    

Now you can run server code in terminal window. It will run until you terminate it (CTRL+C). Next, in another terminal, 
you can run a client code. You should see how values are changing on server side, just by writing memory variables on the 
client side. You can terminate client application by pressing CTRL+C.

Also, you can import client code to play with memory variables by yourself. Open python interactive shell:

.. code-block:: python

    >>> from ex_client_mapper import *
    >>>
    >>> # read ERROR_STATE variable
    >>> print(mem.ERROR_STATE)
    True
    >>> # read it again and you will likely see other value
    >>> # because server constanly alters this variable
    >>> print(mem.ERROR_STATE)
    False
    >>> # write a value to CONTROL_WORD and watch server side
    >>> mem.CONTROL_WORD = 25
    >>>
    >>> # kill the worker when you are done
    >>> client.kill()
    >>> exit()

Now, when you are more familiar with MSM, we can emphasize some notes:

 1. **Memory variables are customizable**
    You declare them on *MemoryStore* instance using special methods of *MemoryVariable* class, and you can give them any name:
 
    .. code-block:: python

        mem.SOME_REALY_STRANGE_NAME = MemoryVariable.byte(address=0, byte_number=0)

 2. **Memory variables have addresses**
    It mean that you can declare two diferent variables, that will overlay. Changing the one will impact the other.
    Doing so sounds strange, but it sometimes has a reason.

    .. code-block:: python

        >>> mem.ONE_VARIABLE = MemoryVariable.byte(address=1, byte_number=0)
        >>> mem.OTHER_VARIABLE = MemoryVariable.byte(address=1, byte_number=0)
        >>> mem.ONE_VARIABLE = 10
        >>> print(mem.OTHER_VARIABLE)
        10
    
    Those above share their address, one is always equal to other and vice versa.

 3. **It is memory what is exchanged, not variables**
    Variables only reflects state of memory. You can declare two variables on one address, or do not declare variables
    at all. Memory still will be exchanged. You can even declare variable later on, and it will still reflect memory 
    state it's pointing on.

 4. **Memory space is Word-numbered**
    Modbus protocol defines holding registers to store 16-bit values. Since we want to be consistent with this standard,
    all addresses are considered to point on 16-bit values (Words).
 
 5. **Client and server runs in separate threads**
    We decided to delegate client/server workers in threads. Those are daemon threds and are started when *.run()* method 
    is called. They should be properly closed, *.kill()* method serves that purpose. Care to call it when you are 
    done with modbus communication.

You see all this facts in given examples. Both: server and client declares exactly the same memory mapping,
but they could do it in a different way - however this would mess up code logic,
but it will work. **It is memory what is exchanged, not variables**. Also, comments in code presents you that 
**memory space is word-numbered**, every register holds 16-bit value. All of this registers **have address**. 
