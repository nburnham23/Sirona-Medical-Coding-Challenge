# Sirona Medical Coding Challenge Assessment

My name is Noah Burnham, and I am applying for the Software Engineer position at Sirona Medical in Burlington, VT. This reposity houses
my Coding Challenge Assessment. 

# Running the project

To run, use `fastapi dev main.py`

# Assumptions


**Question:** What HTTP status codes should errors use, since the spec just says "an appropriate error"?

**Assumption:** 404 for a case/employee that doesn't exist, 409 Conflict for an invalid status transition (claiming a non-PENDING case, reporting a non-IN_PROGRESS case) or a duplicate username, 403 Forbidden when a real employee tries to report a case they didn't claim, and 422 for missing/empty request fields (handled automatically by Pydantic validation).

**Question:** Are `modality` and `status` free-form strings, or a fixed set of values?

**Assumption:** Treated as strict enums (`CT`/`MRI`/`XR`/`US` and `PENDING`/`IN_PROGRESS`/`COMPLETED`) rather than arbitrary strings, so an invalid value is rejected at the API boundary with a 422 instead of being silently stored.

**Question:** Is username uniqueness case-sensitive?

**Assumption:** Yes — `jsmith` and `JSmith` are treated as distinct usernames.

**Question:** Are case/employee ids client-supplied or server-generated?

**Assumption:** Server-generated auto-incrementing integers. Clients never choose or submit an id.

**Question:** What happens to a case if the employee who claimed it is later deleted?

**Assumption:** The case itself is untouched (status and claimedAt stay as they were), but since the employee record is gone, that case's `claimedBy` will show as `null` in future API responses. Deleting an employee does not cascade to or block deletion because of their claimed cases.

**Question:** Should filtering `GET /cases?claimedBy=<username>` error if that username doesn't exist?

**Assumption:** No — it returns an empty list (`{"data": []}`) rather than a 404. An unknown username is treated as "no cases match," not a client error.
