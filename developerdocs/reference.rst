API Reference
~~~~~~~~~~~~~


Serializations
==============

Responses from the MLTSHP API are :mimetype:`application/json` responses that represent the various MLTSHP API objects. Those objects are:


.. entity:: shake

   A shake is a stream of files posted to MLTSHP by users. Shakes can be user shakes, which every user has one of, or group shakes that can have multiple posters.

   :key id: the shake's numeric shake ID as a number
   :key name: the display title of the shake
   :key owner: the :entity:`user` who created the shake
   :key url: the URL of the shake on the MLTSHP site
   :key thumbnail_url: the URL of the shake's thumbnail logo image
   :key description: the shake's description displayed under its logo on its page (optional)
   :key type: the type of shake: either ``user`` or ``group``
   :key created_at: the :entity:`time <timestamp>` when the shake was first created
   :key updated_at: the :entity:`time <timestamp>` when the shake was last updated


.. entity:: sharedfile

   A file that someone posted to a shake. A file can be either an image or a link to a video.

   :key sharekey: the :entity:`sharekey` of the shared file
   :key name: the filename of the shared file
   :key user: the :entity:`user` who shared the file
   :key title: the custom title the poster gave the file (optional)
   :key description: the caption displayed under the file on its page (optional)
   :key posted_at: the :entity:`time <timestamp>` the file was posted
   :key permalink_page: the URL where the file can be viewed on MLTSHP
   :key width: the width of the file (image or video embed) in pixels as a number
   :key height: the height of the file (image or video embed) in pixels as a number
   :key views: the number of times the image has been viewed
   :key likes: the number of times the image has been "liked" to someone's favorites
   :key saves: the number of times the image has been saved to another shake
   :key comments: the number of :entity:`comments <comment>` on the file
   :key nsfw: whether the file has been marked NSFW, and so is hidden by default when displayed on MLTSHP (`true` for NSFW/hidden, `false` for SFW/visible)
   :key original_image_url: if the file is an image, the URL of the image on MLTSHP
   :key url: if the file is *not* an image, the original URL of the shared item
   :key pivot_id: a key that is used for pagination. It varies based on the API method.
   :key saved: flag indicating whether authenticated user has already saved the sharedfile
   :key liked: flag indicating whether authenticated user has already liked the sharedfile


.. entity:: sharekey

   The alphanumeric ID of a :entity:`sharedfile`, such as ``GK4N``. These are the codes in the permalink page (and image URL) of files posted to MLTSHP.


.. entity:: timestamp

   Timestamps represent particular times when events occurred, such as users posting files to shakes. Timestamps are always represented in the MLTSHP API as ISO8601 timestamps in UTC (where the timezone is ``Z``) with resolution to seconds (no microseconds).


.. entity:: user

   A person with a MLTSHP account. Users own or manage shakes and post files in them.

   :key id: the user's numeric user ID as a number
   :key name: the user's username
   :key profile_image_url: the URL to the user's profile picture
   :key about: a brief text blurb about the user. Only available when querying the user resource.
   :key website: the user's URL. Only available when querying the user resource.
   :key shakes: the list of shakes that belong to the user, including their main user shake. Only available when querying the user resource.


.. entity:: comment

   A traditional comment associated with a :entity:`sharedfile`.

   :key body: the actual text body of the comment
   :key user: the :entity:`user` that posted the comment
   :key posted_at: the :entity:`time <timestamp>` when the comment was posted

Resources
=========

The resources (URL endpoints) in the MLTSHP API are:


.. http:get:: /api/favorites
.. http:get:: /api/favorites/before/(beforekey)
.. http:get:: /api/favorites/after/(afterkey)

   Returns the files the authorized user has "liked" most recently (or as specified).

   Use the :samp:`before/{beforekey}` and :samp:`after/{afterkey}` variations to page through the user's favorites. That is, specify the last :entity:`pivot_id` as the key to the :samp:`before/{beforekey}` resource to get the page of files the user "liked" before the current page.

   :param beforekey: the :entity:`pivot_id` of the file to show posts before
   :param afterkey: the :entity:`pivot_id` of the file to show posts after
   :status 200: the response is the requested section of the user's favorites as an object containing:

                * **favorites** – a list of :entity:`sharedfiles <sharedfile>`


.. http:get:: /api/friends
.. http:get:: /api/friends/before/(beforekey)
.. http:get:: /api/friends/after/(afterkey)

   Returns the files posted most recently (or as specified) by the users whom the authorized user follows.

   Use the :samp:`before/{beforekey}` and :samp:`after/{afterkey}` variations to page through the user's friend shake. That is, to request the next page of a friend shake, specify the last :entity:`pivot_id` in the current page as the key to a :samp:`/api/friends/before/{beforekey}` request.

   :param beforekey: the :entity:`pivot_id` of the post to show posts before
   :param afterkey: the :entity:`pivot_id` of the post to show posts after
   :status 200: the response is the requested section of friend shake as an object containing:

                * **friend_shake** – a list of :entity:`sharedfiles <sharedfile>`


.. http:get:: /api/magicfiles
.. http:get:: /api/magicfiles/before/(beforekey)
.. http:get:: /api/magicfiles/after/(afterkey)

   Returns the 10 most recent files accepted by the "magic" file selection algorithm. Currently any files with 10 or more likes are magic.

   Use the :samp:`before/{beforekey}` and :samp:`after/{afterkey}` variations to page through the sharedfiles. That is, specify the last :entity:`pivot_id` as the key to the :samp:`before/{beforekey}` resource to get the page of files saved before the current page.

   :param beforekey: the :entity:`pivot_id` of the file to show posts before
   :param afterkey: the :entity:`pivot_id` of the file to show posts after

   :status 200: the response is the latest magic files as an object containing:

                * **magicfiles** – a list of :entity:`sharedfiles <sharedfile>`


.. http:get:: /api/incoming
.. http:get:: /api/incoming/before/(beforekey)
.. http:get:: /api/incoming/after/(afterkey)

   Returns the 10 most recently posted sharedfiles.

   Use the :samp:`before/{beforekey}` and :samp:`after/{afterkey}` variations to page through the sharedfiles. That is, specify the last :entity:`pivot_id` as the key to the :samp:`before/{beforekey}` resource to get the page of files saved before the current page.

   :param beforekey: the :entity:`pivot_id` of the file to show posts before
   :param afterkey: the :entity:`pivot_id` of the file to show posts after

   :status 200: the response is the latest files as an object containing:

                * **incoming** – a list of :entity:`sharedfiles <sharedfile>`


.. http:get:: /api/shakes/(id)
.. http:get:: /api/shakes/(id)/before/(beforekey)
.. http:get:: /api/shakes/(id)/after/(afterkey)

   Returns the sharedfiles for the specified shake in reverse chronological order.

   Use the :samp:`before/{beforekey}` and :samp:`after/{afterkey}` variations to page through the sharefiles. That is, specify the last :entity:`pivot_id` as the key to the :samp:`before/{beforekey}` resource to get the page of files saved before the current page.

   :param beforekey: the :entity:`pivot_id` of the file to show posts before
   :param afterkey: the :entity:`pivot_id` of the file to show posts after

   :status 200: the response is the requested section of shake's sharedfiles:

                * **sharedfiles** – a list of the :entity:`shake's <shake>` :entity:`sharedfiles <sharedfile>`

   :status 401: authentication failed


.. http:get:: /api/shake_id/(int:shakeid)

   Returns information for the shake with the given numeric shake ID.

   :param shakeid: the shake's numeric ID
   :type userid: int
   :status 200: the response is the requested :entity:`shake`
   :status 404: no such shake with that ID


.. http:get:: /api/shake_name/(shakepathname)

   Returns information for the shake with the given pathname.

   Note that name in this case refers to the URL path to the shake. e.g., for https://mltshp.com/weloveamberandandre the pathname is `weloveamberandandre`.

   :param shakepathname: the shake's pathname
   :status 200: the response is the requested :entity:`shake`
   :status 404: no such shake with that pathname


.. http:get:: /api/shake_user/(username)

   Returns information for the shake belonging to the specified user.

   :param username: the user's username
   :status 200: the response is the requested :entity:`shake`
   :status 404: no such user with that name


.. http:get:: /api/shakes

   Returns the authorized user's shakes.

   :status 200: the response is an object containing:

                * **shakes** – a list of the user's :entity:`shakes <shake>`

   :status 401: authentication failed


.. http:get:: /api/sharedfile/(sharekey)

   Returns information for the file with the given share key.

   :param sharekey: the :entity:`sharekey` of the file
   :status 200: the response is a :entity:`sharedfile` for the requested file
   :status 404: no such file with that share key

.. http:post:: /api/sharedfile/(sharekey)

   Update sharedfile's editable details.

   :param sharekey: the :entity:`sharekey` of the file
   :form title: text for the image title (optional)
   :form description: text for the image description (optional)

   :status 200: the response is a :entity:`sharedfile` for the requested file
   :status 403: the file could not be updated due to permission issues
   :status 404: no such file with that share key


.. http:post:: /api/sharedfile/(sharekey)/like

   "Likes" the file with the given sharekey as the authorized user. The file is then available in the user's favorites.

   :param sharekey: the :entity:`sharekey` of the file to like
   :status 200: the file was liked, and the response is the liked :entity:`sharedfile`
   :status 400: the file could not be liked, probably because the authorized user already liked it
   :status 404: no such file with that share key


.. http:post:: /api/sharedfile/(sharekey)/save

   "Saves" the file with the given sharekey as the authorized user. By default the file is saved to the user's shake
   unless the shake_id parameter is provided.

   :param sharekey: the :entity:`sharekey` of the file to save
   :form shake_id: the id of the destination :entity:`shake` the file should be saved to (optional)
   :status 200: the file was saved, and the response is the saved :entity:`sharedfile`
   :status 400: the file could not be saved, probably because the file belongs to the authenticated user
   :status 403: the file could not be saved due to permission issues
   :status 404: no such file with that share key or no such shake


.. http:get:: /api/sharedfile/(sharekey)/comments

   Returns a list of :entity:`comments <comment>` for the sharedfile with the given sharekey.

   :param sharekey: the :entity:`sharekey` of the file
   :status 404: no such file with that :entity:`sharekey` or no such shake
   :status 200: an object containing:

                * **comments** – a list of :entity:`comments <comment>`

.. http:post:: /api/sharedfile/(sharekey)/comments

   Posts a new :entity:`comment <comment>` on behalf of the authenticated user to the :entity:`sharedfile` referenced with the given :entity:`sharekey`.

   :param sharekey: the :entity:`sharekey` of the file
   :form body: the text contents of the :entity:`comment <comment>`
   :status 404: no such file with that :entity:`sharekey` or no such shake
   :status 400: the comment could not be saved due to a missing parameter or failed spam check
   :status 200: the newly posted :entity:`comment <comment>` object

.. http:post:: /api/upload

   Adds the submitted image to a shake. Images should be provided as :mimetype:`multipart/form-data` request bodies.

   :form file: the file data of the image to upload
   :form shake_id: numeric ID of the shake to post to (optional)
   :form title: text for the image title (optional)
   :form description: text for the image description (optional)
   :status 201: the image was posted to the shake, and the response body is an abbreviated :entity:`sharedfile` representing it, containing only :entity:`sharekey` and name
   :status 400: the file could not be identified as an image


.. http:get:: /api/user

   Returns the authorized user.

   :status 200: the response is the requested :entity:`user`


.. http:get:: /api/user_id/(int:userid)

   Returns information for the user with the given numeric user ID.

   :param userid: the user's numeric ID
   :type userid: int
   :status 200: the response is the requested :entity:`user`
   :status 404: no such user with that ID


.. http:get:: /api/user_name/(username)

   Returns the user with the given username.

   :param username: the user's username
   :status 200: the response is the requested :entity:`user`
   :status 404: no such user with that name
