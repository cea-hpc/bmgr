# List aliases

Used to list aliases.

**URL** : `/api/v1.0/aliases`

**Method** : `GET`

**Data constraints**: None

## Success Response

**Code** : `200 OK`

**Content example**

```json
[
    {
      "name": "aliasA",
      "overrides": {},
      "target": "targetA"
    },
    {
      "name": "aliasB",
      "overrides": {
        "hostA": {
	  "target": "overrideA",
 	  "autodelete": True
  	}
      },
      "target": "targetB"
    }
]
```

# Get alias

Used to get a single alias.

**URL** : `/api/v1.0/aliases/:alias`

**Method** : `GET`

**Data constraints**: None

## Success Response

**Code** : `200 OK`

**Content example**

```json
    {
      "name": "aliasB",
      "overrides": {
        "hostA": {
	  "target": "overrideA",
 	  "autodelete": True
  	}
      },
      "target": "targetB"
    }
```

# Delete alias

Used to delete alias.

**URL** : `/api/v1.0/alias/:alias`

**Method** : `DELETE`

**Data constraints**: None

## Success Response

**Code** : `204 No Content`

# Delete alias override

Used to delete an alias override.

**URL** : `/api/v1.0/alias/:alias/:hostname`

**Method** : `DELETE`

**Data constraints**: None

## Success Response

**Code** : `204 No Content`

# Add alias

Used to add hosts.

**URL** : `/api/v1.0/aliases`

**Method** : `POST`

**Data constraints**:

```json
{
    "name": "[valid alias name]",
    "target": "[A valid target resource]",
}
```

**Data example**

```json
{
  "name": "aliasA",
  "target": "targetA"
}
```

## Success Response

**Code** : `200 OK`

**Content example**

```json
{}
```

## Error Response

**Condition** : If 'alias' already exists

**Code** : `409 CONFLICT`

**Content** : `Alias already exists`

# Add alias override

Used to add hosts.

**URL** : `/api/v1.0/aliases/:alias`

**Method** : `POST`

**Data constraints**:

```json
{
    "hosts": "[valid nodeset]",
    "target": "[A valid target resource]",
    "autodelete": [A Boolean]
}
```

**Data example**

```json
{
    "hosts": "host[1-3]",
    "target": "overrideA",
    "autodelete": True
}
```

## Success Response

**Code** : `200 OK`

**Content example**

```json
{}
```

## Error Response

**Condition** : If 'alias' already exists

**Code** : `409 CONFLICT`

**Content** : `Alias or override already exists`
