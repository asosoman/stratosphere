# stratosphere

# About

From xls to CloudFront through Troposphere.

(In construction - Documentation lacking)

USAGE: stratosphere.py file -sheet sheet
If no sheet is introduced, will use the first one.

We needed a better, more visual, way to create AWS CF descriptions.
Troposhere is a good error catching and makes it easier, but is not really very "visual".

In this case, we use a xls file. (on which an small project fits on a sheet)
You can use different sheets for having a better structure of your site and an easier way to create the templates.

There is the following statements that go in the first column of any row, and the rows are processed in order:
- "vars": create a variable on a dictionary. Can be used later to use that dictionary.
- "params": creates a CF param. Anywhere where found that param, is transformed to the correct Ref or Join AWS CF function.
- Any of the services of troposphere (using the abbreviation) creates an object, adds it to the template, and can be later used anywhere (Ref automatically included).
- "default": allows to use defaults for any of the above services.
- "include": add the named sheet to this description.

Second column is the name of the vars/params/services/default/include.

The other columns are the list of values for that statement. Using the last header found. (header is a list of keys, having the first two columns blank, used on all the subsequent items unless a new header is found)
