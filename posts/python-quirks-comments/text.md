# Python Quirks: Comments

```python
# I'm a comment.

"""
I'm also a comment.
"""

"I'm a comment too!"

87_104_121_32_97_109_32_73_32_97_32_99_111_109_109_101_110_116_63

["I'm", "also", "a", "comment", ("surprisingly.",)]
```  
<figcaption>Totally valid Python program.</figcaption>

Only one of these “comments” is a real one. 
Well, technically speaking all of them are comments, the real difference between them is speed and functionality.

Let's generate some code to find out what the actual differences between them are.

```python
from time import time

# style comments
real_comments_code = ""
"string literal style comments"
fake_comments_code = ""

for comment_id in range(500000):
	comment = "I'm comment number %i" % comment_id

	real_comments_code += "# %s\n" % comment
	fake_comments_code += '"%s"\n' % comment

start_time = time()
compile(real_comments_code, "<string>", "exec")
print("Real comments took: %s" % (time() - start_time))

start_time = time()
compile(fake_comments_code, "<string>", "exec")
print("Fake comments took: %s" % (time() - start_time))
```
<figcaption>Executing speed comparison (real comments vs. fake comments).</figcaption>

```
Real comments took: 0.08859992027282715
Fake comments took: 1.4969751834869385
```

The “#” comment variant is clearly favorable over the isolated string literal one in this completely unrealistic scenario, so if you ever wanted to include 500000 comments in your code, they are clearly the way to go.

But what's actually happening here, and because this is Python, can we somehow abuse this behavior? Let's examine the AST of our two automatically generated programs to find out.

```
Module
```
<figcaption>Syntax tree for real comments</figcaption>

```
Module
  Expr
    Str
  Expr
    Str
  Expr
    Str
  Expr
    Str
  Expr
    Str
  ...
```
<figcaption>Syntax tree for fake comments</figcaption>

Real comments are simply left out of the final Python AST, just as one would expect. That's exactly where the speed difference is taking place, string literals still need to be evaluated on program runtime and you should never abuse them for comments. But that doesn't mean that they are useless.

```python
def documented_function():
	# I'm __doc__
	"No, I'm __doc__!"
	"""
	Shut up you two, I'm the real __doc__ here! (well, maybe not)
	"""
	print("I'm a documented function.")

print(documented_function.__doc__)
```
<figcaption>"No, I'm __doc__!" (""" style docstrings are the preferred in the spec)</figcaption>

Citing [PEP-0257](https://www.python.org/dev/peps/pep-0257/):
> A docstring is a string literal that occurs as the first statement in a module, function, class, or method definition. Such a docstring becomes the __doc__ special attribute of that object.

Python not only supports isolated strings literals, it essentially supports isolated anything. What's interesting here is, that all statements are evaluated. In combination with properties this behavior allows for some very “Ruby-esque” code.

```python
class ClassWithProperty:
	def __init__(self, lazy=True):
		self._instance_property = None

		if not lazy:
			self.instance_property


	@property
	def instance_property(self):
		if self._instance_property == None:
			print("Working hard, but I'm still lazy.")
			self._instance_property = "I was born lazy."
		return self._instance_property

ClassWithProperty(lazy=False)
ClassWithProperty()
```
<figcaption>"Ruby-esque" lazy loading</figcaption>

In conclusion: **Don’t abuse the language** (well, a little can’t hurt, right?)