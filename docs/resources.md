# List resources

Used to list resources.

**URL** : `/api/v1.0/resources`

**Method** : `GET`

**Data constraints**: None

## Success Response

**Code** : `200 OK`

**Content example**

```json
[
    {
      "name": "resourceA",
      "template_uri": "file://resourceA.jinja"
    },
    {
      "name": "resourceB",
      "template_uri": "file://resourceB.jinja"
    }
]
```

# Get resource

Used to get a single resource.

**URL** : `/api/v1.0/resources/:resource`

**Method** : `GET`

**Data constraints**: None

## Success Response

**Code** : `200 OK`

**Content example**

```json
{
  "name": "resourceA",
  "template_uri": "file://resourceA.jinja"
}
```

# Delete resource

Used to delete resources.

**URL** : `/api/v1.0/resources/:resource`

**Method** : `DELETE`

**Data constraints**: None

## Success Response

**Code** : `204 No Content`

# Add resources

Used to add hosts.

**URL** : `/api/v1.0/resources`

**Method** : `POST`

**Data constraints**:

```json
{
    "name": "[valid resource name name]",
    "template uri": "[A valid template URI]"
}
```

**Data example**

```json
{
  "name": "resourceA",
  "template_uri": "file://resourceA.jinja"
}
```

## Success Response

**Code** : `200 OK`

**Content example**

```json
{
  "name": "resourceA",
  "template_uri": "file://resourceA.jinja"
}
```

## Error Response

**Condition** : If 'resource' already exists

**Code** : `409 CONFLICT`

**Content** : "Resource already exists"

# Update resources

Used to update resources.

**URL** : `/api/v1.0/resources/:resource`

**Method** : `PATCH`

**Data constraints**:

```json
{
    "template uri": "[A valid template URI]"
}
```

**Data example**

```json
{
  "template_uri": "file://resourceA.jinja"
}
```

## Success Response

**Code** : `200 OK`

**Content example**

```json
{
  "name": "resourceA",
  "template_uri": "file://resourceA.jinja"
}
```

# Render resource

Used to render a resource for the given host.

**URL** : `/api/v1.0/resources/:resource/:hostname`

**Method** : `GET`

**Data constraints**: None

## Success Response

**Code** : `200 OK`

**Content example**

```
#!ipxe
The rendered script
```

## Error Response

**Condition** : If 'resource' does not exists

**Code** : `400 BAD REQUEST`

**Content** : "Template not found on server: :exception_traceback"

## Error Response

**Condition** : If an error occured while rendering the template

**Code** : `400 BAD REQUEST`

**Content** : "Error whiel rendering template: :exception_traceback"
