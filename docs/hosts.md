# List hosts

Used to list registered hosts.

**URL** : `/api/v1.0/hosts`

**Method** : `GET`

**Data constraints**: None

## Success Response

**Code** : `200 OK`

**Content example**

```json
[
    {
      "name": "host1",
      "profiles": ["profileA", "profileB"],
      "attributes": {"attributeA": 1, "attributeB": 2}
    },
    {
      "name": "host[2-3]",
      "profiles": ["profileA", "profileC"],
      "attributes": {"attributeA": 1, "attributeC": 3}
    }
]
```

# Get host

Used to get a single host.

**URL** : `/api/v1.0/hosts/:hostname`

**Method** : `GET`

**Data constraints**: None

## Success Response

**Code** : `200 OK`

**Content example**

```json
[
    {
      "name": "host1",
      "profiles": ["profileA", "profileB"],
      "attributes": {"attributeA": 1, "attributeB": 2}
    }
]
```

# Add host

Used to add hosts.

**URL** : `/api/v1.0/hosts`

**Method** : `POST`

**Data constraints**:

```json
{
    "name": "[valid NodeSet]",
    "profiles": [
      "[A existing profile]",
      "[A second profile]",
    ]
}
```

**Data example**

```json
{
    "name": "host[1-3]",
    "profiles": [
      "profileA",
      "profileB",
    ]
}
```

## Success Response

**Code** : `200 OK`

**Content example**

```json
[
    {
      "name": "host[1-3]",
      "profiles": ["profileA", "profileB"]
    }
]
```

## Error Response

**Condition** : If 'host' already exists

**Code** : `409 CONFLICT`

**Content** : `Host already exists`

# Delete host

Used to delete hosts.

**URL** : `/api/v1.0/hosts/:hostname`

**Method** : `DELETE`

**Data constraints**: None

## Success Response

**Code** : `204 No Content`

# Update host

Used to update hosts.

**URL** : `/api/v1.0/hosts/:hostname`

**Method** : `PATCH`

**Data constraints**:

```json
{
    "profiles": [
      "[A existing profile]",
      "[A second profile]",
    ]
}
```

**Data example**

```json
{
    "profiles": [
      "profileA",
      "profileB",
    ]
}
```

## Success Response

**Code** : `200 OK`

**Content example**

```json
[
    {
      "name": "host1",
      "profiles": ["profileA", "profileB"]
    }
]
```
