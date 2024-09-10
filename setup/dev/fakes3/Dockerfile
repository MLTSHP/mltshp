FROM ruby:2.7 as builder

ENV FAKES3_VERSION 2.0.0

RUN gem install fakes3 -v ${FAKES3_VERSION} \
    && rm -rf /usr/local/bundle/cache/*

FROM ruby:2.7-slim

COPY --from=builder /usr/local/bundle /usr/local/bundle/

VOLUME /srv
RUN mkdir -p /srv \
    && chown nobody:nogroup /srv \
    && chmod 750 /srv \
    && ln -s /usr/local/bundle/bin/fakes3 /usr/bin/fakes3
WORKDIR /srv

EXPOSE 4567

USER nobody
ENTRYPOINT ["fakes3", "--port", "4567"]
CMD ["--root", "/srv"]
