# Common component modules

Modules in this folder define and implement classes and member
functions that are identical whether a model is run using the
prototyping implementation or the NES API implementation.

Put as many of the definitions and implementations here as
possible in order to minimize the quantity of code that can
diverge as prototyping code continues to develop.

Typical call structure:

```
model code
          --> prototyping specific
                                  --> common component code

```

To further simplify and increase the amount of code placed here,
reference dictionaries can be used in common classes so that
prototyping or NES API specific objects can be created and
called from common code. For example, see the `compObjRef`
dictionary in `_BSAlignedNC`.

--
Randal A. Koene, 20240101
