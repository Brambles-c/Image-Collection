import aiohttp, asyncio

class Fetcher:
    def __init__(self):
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=2)
        )
    
    async def close(self):
        await self.session.close()

    def _error(self, identifier):
        image_id = identifier.split("/")[-1]
        print(f"\nhttps://derpibooru.org/images/{image_id}")


    async def _fetch(self, identifier, image_format, retries, alt_retrying = False):
        url = f"https://derpicdn.net/img{"/view" if alt_retrying else ""}/{identifier}{"/medium" if not alt_retrying else ""}.{image_format}"

        for i in range(retries + 1):
            await asyncio.sleep(i ** 2 * 5)

            try:
                resp = await self.session.get(url, timeout=10)

                if resp.status == 404:
                    if not alt_retrying:
                        return await self._fetch(identifier, image_format, retries, alt_retrying=True)
                    
                    image_id = identifier.split("/")[-1]

                    print(f"\nFailed to fetch for #{image_id}\n")
                    print(resp.status)
                    print(await resp.read())
                    return None

                elif resp.status == 520:
                    return await self._fetch(identifier, image_format, 0, alt_retrying)

                elif resp.status != 200:
                    print(f"\nFailed to get image from url: {url}")
                    print(resp.status, resp, await resp.read(), "\n")
                    self._error(identifier)
                    return False

                return await resp.read()
            except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as e:
                if i == 0: print()
                print(f"Retrying due to {type(e).__name__}...")
                continue
            except Exception as e:
                print()
                print(e)
                self._error(identifier)
                return False
        else:
            self._error(identifier)
            return False

    async def fetch(self, identifier, image_format, retries=2):
        return await self._fetch(identifier, image_format, retries)
