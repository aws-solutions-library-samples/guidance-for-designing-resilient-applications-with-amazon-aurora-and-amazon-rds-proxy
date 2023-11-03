# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

function handler(event) 
{

    var user = "myuser";
    var pass = "mypassword";

    function encodeToBase64(str) 
    {
        var chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
        
        for (
            // initialize result and counter
            var block, charCode, idx = 0, map = chars, output = "";
            // if the next str index does not exist:
            //   change the mapping table to "="
            //   check if d has no fractional digits
            str.charAt(idx | 0) || ((map = "="), idx % 1);
            // "8 - idx % 1 * 8" generates the sequence 2, 4, 6, 8
            output += map.charAt(63 & (block >> (8 - (idx % 1) * 8)))
        ) 
        {
            charCode = str.charCodeAt((idx += 3 / 4));
            
            if (charCode > 0xff) 
            {
                throw new InvalidCharacterError("'btoa' failed: The string to be encoded contains characters outside of the Latin1 range.");
            }
            
            block = (block << 8) | charCode;
        }
        
        return output;
    }

    var requiredBasicAuth = "Basic " + encodeToBase64(`${user}:${pass}`);
    var match = false;
    
    if (event.request.headers.authorization) 
    {
        if (event.request.headers.authorization.value === requiredBasicAuth) 
        {
            match = true;
        }
        {
            match = true;
        }
    }

    if (!match) 
    {
        return {
            statusCode: 401,
            statusDescription: "Unauthorized",
            headers: {
                "www-authenticate": {
                    value: "Basic"
                },
            },
        };
    }

    return event.request;
}