Protocol Droid is aimed at being a universal protocol bridge. It's first mission is to provide HTTP interfaces to other protocols. However, the long term goal is to have arbitrary bridges. Of course, the idea is to add them as needed for actual use cases. This is why the initial goal is to focus on HTTP based bridges, since this is a very practical use with all this webhook and cloud-side code business.

Supported (yet likely incomplete) outgoing connection interfaces:
 * HTTP-Socket
 * HTTP-SMTP

Supported (yet likely incomplete) listening interfaces:
 * HTTP-SMTP

Prototcol wishlist:
 * IMAP
 * IRC
 * FTP
 * SSH
 * XMPP
 * DNS?
 * LDAP