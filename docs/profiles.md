# List profiles

Used to list profiles.

**URL** : `/api/v1.0/profiles`

**Method** : `GET`

**Data constraints**: None

## Success Response

**Code** : `200 OK`

**Content example**

```json
[
    {
      "name": "profileA",
      "attributes": {
          "attr1": "val1",
          "attr2": "val2"
      },
      "weight": 0
    },
    {
      "name": "profileB",
      "attributes": {
          "attr1": "val1_bis",
      },
      "weight": 10
    },
]
```

# Get profile

Used to get a single profile.

**URL** : `/api/v1.0/profiles/:profile`

**Method** : `GET`

**Data constraints**: None

## Success Response

**Code** : `200 OK`

**Content example**

```json
{
  "name": "profileA",
  "attributes": {
      "attr1": "val1",
      "attr2": "val2"
  },
  "weight": 0
}
```

# Delete profile

Used to delete profiles.

**URL** : `/api/v1.0/profiles/:profile`

**Method** : `DELETE`

**Data constraints**: None

## Success Response

**Code** : `204 No Content`


# Add profiles

Used to add profiles.

**URL** : `/api/v1.0/profiles`

**Method** : `POST`

**Data constraints**:

```json
{
    "name": "[valid profile name]",
    "attributes": {
      "[attribute name}": "[attribute value]",
      "[attribute name}": "[attribute value]"
    },
    "weight": [An integer]
}
```

**Data example**

```json
{
  "name": "profileA",
  "attributes": {
      "attr1": "val1",
      "attr2": "val2"
  },
  "weight": 10
}
```

## Success Response

**Code** : `200 OK`

**Content example**

```json
{
  "name": "profileA",
  "attributes": {
      "attr1": "val1",
      "attr2": "val2"
  },
  "weight": 10
}
```

## Error Response

**Condition** : If 'profile' already exists

**Code** : `409 CONFLICT`

**Content** : `Profile already exists`

# Update profiles

Used to update profiles.

**URL** : `/api/v1.0/profiles/:profile`

**Method** : `PATCH`

**Data constraints**:

```json
{
    "attributes": {
      "[attribute name}": "[attribute value]",
      "[attribute name}": "[attribute value]"
    },
    "weight": [An integer]
}
```

**Data example**

```json
{
  "attributes": {
      "attr1": "val1",
      "attr2": "val2"
  },
  "weight": 10
}
```

## Success Response

**Code** : `200 OK`

**Content example**

```json
{
  "name": "profileA",
  "attributes": {
      "attr1": "val1",
      "attr2": "val2"
  },
  "weight": 10
}
```

