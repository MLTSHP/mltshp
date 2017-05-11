import handlers

routes = [
    (r"/(before|after)/([A-Z0-9]+)?/?(returning)?", handlers.home.HomeHandler),
    (r"/", handlers.home.HomeHandler),

    (r"/ad", handlers.misc.AdBannerHandler),
    (r"/api/authorize", handlers.api.AuthorizeHandler),
    (r"/api/token", handlers.api.TokenHandler),
    (r"/api/sharedfile/([a-zA-Z0-9]+)", handlers.api.SharedfileHandler),
    (r"/api/sharedfile/([a-zA-Z0-9]+)/like",
        handlers.api.SharedfileLikeHandler),
    (r"/api/sharedfile/([a-zA-Z0-9]+)/save",
        handlers.api.SharedfileSaveHandler),
    (r"/api/sharedfile/([a-zA-Z0-9]+)/comments",
        handlers.api.SharedfilesCommentsHandler),
    (r"/api/(user_name|user_id)/([a-zA-Z0-9_\-]+)",
        handlers.api.UserHandler),
    (r"/api/(user)", handlers.api.UserHandler),
    (r"/api/shakes", handlers.api.UserShakesHandler),
    (r"/api/shakes/([0-9]+)", handlers.api.ShakeStreamHandler),
    (r"/api/shakes/([0-9]+)/(before|after)/([\a-zA-Z0-9]+)",
        handlers.api.ShakeStreamHandler),
    (r"/api/friends", handlers.api.FriendShakeHandler),
    (r"/api/friends/(before|after)/([\a-zA-Z0-9]+)",
        handlers.api.FriendShakeHandler),
    (r"/api/upload", handlers.api.FileUploadHandler),
    (r"/api/internalupload", handlers.api.FileUploadHandler),
    (r"/api/magicfiles", handlers.api.MagicfilesHandler),
    (r"/api/magicfiles/(before|after)/([0-9]+)",
        handlers.api.MagicfilesHandler),
    (r"/api/favorites", handlers.api.FavoritesHandler),
    (r"/api/favorites/(before|after)/([a-zA-Z0-9]+)",
        handlers.api.FavoritesHandler),
    (r"/api/incoming", handlers.api.IncomingHandler),
    (r"/api/incoming/(before|after)/([a-zA-Z0-9]+)",
        handlers.api.IncomingHandler),

    (r"/developers/?", handlers.developers.PageHandler),
    (r"/developers/(guide|reference)", handlers.developers.PageHandler),
    (r"/developers/apps", handlers.developers.AppsListHandler),
    (r"/developers/new-api-application?", handlers.developers.NewAppHandler),
    (r"/developers/view-app/([\d]+)", handlers.developers.ViewAppHandler),
    (r"/developers/edit-app/([\d]+)", handlers.developers.EditAppHandler),

    (r"/friends/(before|after)/([A-Z0-9]+)?", handlers.friends.FriendHandler),
    (r"/friends", handlers.friends.FriendHandler),

    (r"/incoming/(before|after)/([A-Z0-9]+)?",
        handlers.incoming.IncomingHandler),
    (r"/incoming/?([\d]+)?", handlers.incoming.IncomingHandler),

    (r"/p/([a-zA-Z0-9]+)/comment/([0-9]+)/delete",
        handlers.image.CommentDeleteHandler),
    (r"/p/([a-zA-Z0-9]+)/comment", handlers.image.CommentHandler),
    (r"/p/([a-zA-Z0-9]+)/nsfw", handlers.image.NSFWHandler),
    (r"/p/([a-zA-Z0-9]+)/save", handlers.image.SaveHandler),
    (r"/p/([a-zA-Z0-9]+)/delete", handlers.image.DeleteHandler),
    (r"/p/([a-zA-Z0-9]+)/saves", handlers.image.ShowSavesHandler),
    (r"/p/([a-zA-Z0-9]+)/likes", handlers.image.ShowLikesHandler),
    (r"/p/([a-zA-Z0-9]+)/quick-comments", handlers.image.QuickCommentsHandler),
    (r"/p/([a-zA-Z0-9]+)/shakes", handlers.image.AddToShakesHandler),
    (r"/p/([a-zA-Z0-9]+)/shakes/([\d]+)/delete",
        handlers.image.DeleteFromShake),
    (r"/p/([a-zA-Z0-9]+)/quick-edit-title",
        handlers.image.QuickEditTitleHandler),
    (r"/p/([a-zA-Z0-9]+)/quick-edit-description",
        handlers.image.QuickEditDescriptionHandler),
    (r"/p/([a-zA-Z0-9]+)/quick-edit-source-url",
        handlers.image.QuickEditSourceURLHandler),
    (r"/p/([a-zA-Z0-9]+)/comment/([0-9]+)/like",
        handlers.image.CommentLikeHandler),
    (r"/p/([a-zA-Z0-9]+)/comment/([0-9]+)/dislike",
        handlers.image.CommentDislikeHandler),

    (r"/p/([a-zA-Z0-9]+)/favor", handlers.image.LikeHandler),
    (r"/p/([a-zA-Z0-9]+)/unfavor", handlers.image.UnlikeHandler),
    (r"/p/([a-zA-Z0-9]+)/like", handlers.image.LikeHandler),
    (r"/p/([a-zA-Z0-9]+)/unlike", handlers.image.UnlikeHandler),
    (r"/p/([a-zA-Z0-9]+)", handlers.image.ShowHandler),
    (r"/r/([a-zA-Z0-9]+)\.?(.*)", handlers.image.ShowRawHandler),
    (r"/services/oembed", handlers.image.OEmbedHandler),

    (r"/shake/create", handlers.shake.CreateShakeHandler),
    (r"/shake/([a-zA-Z0-9\-]+)/members", handlers.shake.MembersHandler),
    (r"/shake/([a-zA-Z0-9\-]+)/update", handlers.shake.UpdateShakeHandler),
    (r"/shake/internalupdate", handlers.shake.UpdateShakeHandler),
    (r"/shake/([a-zA-Z0-9\-]+)/subscribe",
        handlers.shake.SubscribeShakeHandler),
    (r"/shake/([a-zA-Z0-9\-]+)/unsubscribe",
        handlers.shake.UnsubscribeShakeHandler),
    (r"/shake/([a-zA-Z0-9\-]+)/invite", handlers.shake.InviteMemberHandler),
    (r"/shake/([a-zA-Z0-9\-]+)/accept-invitation",
        handlers.shake.AcceptInvitationHandler),
    (r"/shake/([a-zA-Z0-9\-]+)/quick-details",
        handlers.shake.QuickDetailsHandler),
    (r"/shake/([a-zA-Z0-9\-]+)/rss", handlers.shake.RSSFeedHandler),
    (r"/shake/([a-zA-Z0-9\-]+)/request_invitation",
        handlers.shake.RequestInvitationHandler),
    (r"/shake/([a-zA-Z0-9\-]+)/approve_invitation",
        handlers.shake.ApproveInvitationHandler),
    (r"/shake/([a-zA-Z0-9\-]+)/decline_invitation",
        handlers.shake.DeclineInvitationHandler),
    (r"/shake/([a-zA-Z0-9\-]+)/quit", handlers.shake.QuitHandler),
    (r"/shake/([a-zA-Z0-9\-]+)/members/remove",
        handlers.shake.RemoveMemberHandler),
    (r"/shake/([a-zA-Z0-9\-]+)/followers/?([\d]+)?",
        handlers.shake.FollowerHandler),

    (r"/tag/([a-zA-Z0-9\-]+)", handlers.tag.TagHandler),
    (r"/tag/([a-zA-Z0-9\-]+)/(before|after)/([a-zA-Z0-9]+)",
        handlers.tag.TagHandler),

    (r"/user/([a-zA-Z0-9_\-]+)/?([\d]+)?",
        handlers.account.AccountImagesHandler),
    (r"/user/([a-zA-Z0-9_\-]+)/subscribe", handlers.account.SubscribeHandler),
    (r"/user/([a-zA-Z0-9_\-]+)/unsubscribe",
        handlers.account.UnsubscribeHandler),
    (r"/user/([a-zA-Z0-9_\-]+)/likes/(before|after)/([0-9]+)?",
        handlers.account.UserLikesHandler),
    (r"/user/([a-zA-Z0-9_\-]+)/likes/?", handlers.account.UserLikesHandler),
    (r"/user/([a-zA-Z0-9_\-]+)/rss", handlers.account.RSSFeedHandler),
    (r"/user/([a-zA-Z0-9_\-]+)/followers/?([\d]+)?",
        handlers.account.FollowerHandler),
    (r"/user/([a-zA-Z0-9_\-]+)/following/?([\d]+)?",
        handlers.account.FollowingHandler),
    (r"/user/([a-zA-Z0-9_\-]+)/counts", handlers.account.FileCountHandler),

    (r"/AdvertisingEyeFaceOpportunity/([a-zA-Z0-9_\-]+)/?([\d]+)?",
        handlers.account.AccountImagesHandler),
    (r"/AdvertisingEyeFaceOpportunity/([a-zA-Z0-9_\-]+)/subscribe",
        handlers.account.SubscribeHandler),
    (r"/AdvertisingEyeFaceOpportunity/([a-zA-Z0-9_\-]+)/unsubscribe",
        handlers.account.UnsubscribeHandler),
    (r"/AdvertisingEyeFaceOpportunity/([a-zA-Z0-9_\-]+)/"
        "likes/(before|after)/([0-9]+)?", handlers.account.UserLikesHandler),
    (r"/AdvertisingEyeFaceOpportunity/([a-zA-Z0-9_\-]+)/likes/?",
        handlers.account.UserLikesHandler),
    (r"/AdvertisingEyeFaceOpportunity/([a-zA-Z0-9_\-]+)/rss",
        handlers.account.RSSFeedHandler),
    (r"/AdvertisingEyeFaceOpportunity/([a-zA-Z0-9_\-]+)/followers/?([\d]+)?",
        handlers.account.FollowerHandler),
    (r"/AdvertisingEyeFaceOpportunity/([a-zA-Z0-9_\-]+)/following/?([\d]+)?",
        handlers.account.FollowingHandler),
    (r"/AdvertisingEyeFaceOpportunity/([a-zA-Z0-9_\-]+)/counts",
        handlers.account.FileCountHandler),

    (r"/~([a-zA-Z0-9_\-]+)/?([\d]+)?",
        handlers.account.AccountImagesHandler),
    (r"/~([a-zA-Z0-9_\-]+)/subscribe",
        handlers.account.SubscribeHandler),
    (r"/~([a-zA-Z0-9_\-]+)/unsubscribe",
        handlers.account.UnsubscribeHandler),
    (r"/~([a-zA-Z0-9_\-]+)/"
        "likes/(before|after)/([0-9]+)?", handlers.account.UserLikesHandler),
    (r"/~([a-zA-Z0-9_\-]+)/likes/?",
        handlers.account.UserLikesHandler),
    (r"/~([a-zA-Z0-9_\-]+)/rss",
        handlers.account.RSSFeedHandler),
    (r"/~([a-zA-Z0-9_\-]+)/followers/?([\d]+)?",
        handlers.account.FollowerHandler),
    (r"/~([a-zA-Z0-9_\-]+)/following/?([\d]+)?",
        handlers.account.FollowingHandler),
    (r"/~([a-zA-Z0-9_\-]+)/counts",
        handlers.account.FileCountHandler),

    (r"/confirm-account/?", handlers.account.ConfirmAccountHandler),
    (r"/sign-in/?", handlers.account.SignInHandler),
    (r"/sign-out/?", handlers.account.SignOutHandler),
    (r"/create-account/?", handlers.account.CreateAccountHandler),
    (r"/verify-email/([a-zA-Z0-9]{40})", handlers.account.VerifyEmailHandler),
    (r"/account/forgot-password", handlers.account.ForgotPasswordHandler),
    (r"/account/reset-password/([a-zA-Z0-9]{40})",
        handlers.account.ResetPasswordHandler),
    (r"/account/settings/connections/([0-9]+)/disconnect",
        handlers.account.SettingsConnectionsHandler),
    (r"/account/settings/connections",
        handlers.account.SettingsConnectionsHandler),
    (r"/account/settings/profile", handlers.account.SettingsProfileHandler),
    # below is for nginx, which will only send POSTs here, via upload module.
    (r"/account/settings/profile/internalsave",
        handlers.account.SettingsProfileHandler),
    (r"/account/settings/profile/save",
        handlers.account.SettingsProfileHandler),
    (r"/account/settings", handlers.account.SettingsHandler),
    (r"/account/redeem", handlers.account.RedeemHandler),
    (r"/account/shakes", handlers.account.ShakesHandler),
    (r"/account/quick-notifications",
        handlers.account.QuickNotificationsHandler),
    (r"/account/quick-send-invitation",
        handlers.account.QuickSendInvitationHandler),
    (r"/account/clear-notification",
        handlers.account.ClearNotificationHandler),
    (r"/account/announcement/(tou)",
        handlers.account.AnnouncementHandler),
    (r"/account/set-content-filter/(on|off)",
        handlers.account.SetContentFilterHandler),
    (r"/account/quick_name_search", handlers.account.QuickNameSearch),
    (r"/account/mlkshk-migrate", handlers.account.MlkshkMigrationHandler),
    (r"/account/welcome-to-mltshp", handlers.account.WelcomeToMltshp),
    (r"/account/membership", handlers.account.MembershipHandler),
    (r"/account/payment/cancel", handlers.account.PaymentCancelHandler),
    (r'/account/settings/resend-verification-email',
        handlers.account.ResendVerificationEmailHandler),
    (r'/account/image-request', handlers.account.RequestImageZipFileHandler),

    (r"/mentions/?([\d]+)?", handlers.conversations.MentionsHandler),
    (r"/conversations/(all|my-files|my-comments)/?([\d]+)?",
        handlers.conversations.IndexHandler),
    (r"/conversations/([\d]+)/mute", handlers.conversations.MuteHandler),
    (r"/conversations/?", handlers.conversations.IndexHandler),

    (r"/faq/?", handlers.misc.FAQHandler),
    (r"/coming-soon/?", handlers.misc.ComingSoonHandler),
    (r"/heartbeat", handlers.misc.HeartbeatHandler),
    ## TODO: needs customization for mltshp.com domain
    #(r"/googlead81c5d028a3e443.html", handlers.misc.WebmasterToolsHandler),
    (r"/styleguide", handlers.misc.StyleguideHandler),
    (r"/terms-of-use", handlers.misc.TermsOfUseHandler),
    (r"/code-of-conduct", handlers.misc.CodeOfConductHandler),
    (r"/healthy/is_healthy.php", handlers.misc.HAProxyHandler),

    (r"/popular", handlers.popular.IndexHandler),
    (r"/popular/([\d]+)", handlers.popular.IndexHandler),

    (r"/admin/?", handlers.admin.IndexHandler),
    (r"/admin/create-users", handlers.admin.CreateUsersHandler),
    (r"/admin/interesting-stats", handlers.admin.InterestingStatsHandler),
    (r"/admin/waitlist", handlers.admin.WaitlistHandler),
    (r"/admin/nsfw-users", handlers.admin.NSFWUserHandler),
    (r"/admin/user/([a-zA-Z0-9_\-]+)/flag-nsfw",
        handlers.admin.FlagNSFWHandler),
    (r"/admin/delete-user", handlers.admin.DeleteUserHandler),
    (r"/admin/recommend-group-shake/?(recommend|unrecommend)?",
        handlers.admin.RecommendedGroupShakeHandler),
    (r"/admin/group-shakes", handlers.admin.GroupShakeListHandler),
    (r"/admin/group-shake/([0-9]+)", handlers.admin.GroupShakeViewHandler),
    (r"/admin/shake-categories", handlers.admin.ShakeCategoriesHandler),
    (r"/admin/new-users", handlers.admin.NewUsers),

    (r"/tools/p", handlers.tools.PickerPopupHandler),
    (r"/tools/plugins", handlers.tools.PluginsHandler),
    (r"/tools/twitter", handlers.tools.ToolsTwitterHandler),
    (r"/tools/twitter/connect", handlers.tools.ToolsTwitterConnectHandler),
    (r"/tools/twitter/how-to", handlers.tools.ToolsTwitterHowToHandler),
    (r"/tools/new-post", handlers.tools.NewPostHandler),
    (r"/tools/save-video", handlers.tools.SaveVideoHandler),
    (r"/tools/bookmarklet", handlers.tools.BookmarkletPageHandler),
    (r"/tools/find-shakes/quick-fetch-twitter",
        handlers.tools.FindShakesQuickFetchTwitter),
    (r"/tools/find-shakes/quick-fetch-category/([a-zA-Z0-9_\-]+)",
        handlers.tools.FindShakesQuickFetchCategory),
    (r"/tools/find-shakes/twitter", handlers.tools.FindShakesTwitter),
    (r"/tools/find-shakes/people", handlers.tools.FindShakesPeople),
    (r"/tools/find-shakes", handlers.tools.FindShakesGroups),

    (r"/upload", handlers.upload.UploadHandler),
    (r"/internalupload", handlers.upload.UploadHandler),

    # the shake handler
    (r"/([a-zA-Z0-9\-]+)", handlers.shake.ShakeHandler),
    (r"/([a-zA-Z0-9\-]+)/(before|after)/([a-zA-Z0-9]+)",
        handlers.shake.ShakeHandler),

    # webhooks
    (r"/webhooks/stripe", handlers.stripe_hooks.StripeWebhook),

    # if we don't have a route match, send it to our 404-designated handler.
    (r".*", handlers.error.NotFoundHandler)
]
