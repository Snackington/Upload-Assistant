# -*- coding: utf-8 -*-
import asyncio
import requests
import platform
import os
from src.trackers.COMMON import COMMON
from src.console import console


class TTR():
    """
    Edit for Tracker:
        Edit BASE.torrent with announce and source
        Check for duplicates
        Set type/category IDs
        Upload
    """

    ###############################################################
    ########                    EDIT ME                    ########
    ###############################################################

    # ALSO EDIT CLASS NAME ABOVE

    def __init__(self, config):
        self.config = config
        self.tracker = 'TTR'
        self.source_flag = 'TTR'
        self.upload_url = 'https://torrenteros.org/api/torrents/upload'
        self.search_url = 'https://torrenteros.org/api/torrents/filter'
        self.banned_groups = [""]
        pass
    
    async def get_cat_id(self, category_name):
        category_id = {
            'MOVIE': '1', 
            'TV': '2', 
            }.get(category_name, '0')
        return category_id

    async def get_type_id(self, type):
        type_id = {
            'DISC': '1', 
            'REMUX': '2',
            'WEBDL': '4', 
            'WEBRIP': '5', 
            'HDTV': '6',
            'ENCODE': '3'
            }.get(type, '0')
        return type_id

    async def get_res_id(self, resolution):
        resolution_id = {
            '8640p':'10', 
            '4320p': '1', 
            '2160p': '2', 
            '1440p' : '3',
            '1080p': '3',
            '1080i':'4', 
            '720p': '5',  
            '576p': '6', 
            '576i': '7',
            '480p': '8', 
            '480i': '9'
            }.get(resolution, '10')
        return resolution_id

    ###############################################################
    ######   STOP HERE UNLESS EXTRA MODIFICATION IS NEEDED   ######
    ###############################################################

    async def upload(self, meta):
        common = COMMON(config=self.config)
        await common.edit_torrent(meta, self.tracker, self.source_flag)
        cat_id = await self.get_cat_id(meta['category'])
        type_id = await self.get_type_id(meta['type'])
        resolution_id = await self.get_res_id(meta['resolution'])
        await common.unit3d_edit_desc(meta, self.tracker)
        region_id = await common.unit3d_region_ids(meta.get('region'))
        distributor_id = await common.unit3d_distributor_ids(meta.get('distributor'))
        if meta['anon'] != 0 or self.config['TRACKERS'][self.tracker].get('anon', False):
            anon = 1
        else:
            anon = 0

        if meta['bdinfo'] != None:
            mi_dump = None
            bd_dump = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/BD_SUMMARY_00.txt", 'r', encoding='utf-8').read()
        else:
            mi_dump = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/MEDIAINFO.txt", 'r', encoding='utf-8').read()
            bd_dump = None
        desc = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/[{self.tracker}]DESCRIPTION.txt", 'r').read()
        open_torrent = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/[{self.tracker}]{meta['clean_name']}.torrent", 'rb')
        files = {'torrent': open_torrent}
        data = {
            'name' : await self.get_name(meta),
            'description' : desc,
            'mediainfo' : mi_dump,
            'bdinfo' : bd_dump, 
            'category_id' : cat_id,
            'type_id' : type_id,
            'resolution_id' : resolution_id,
            'tmdb' : meta['tmdb'],
            'imdb' : meta['imdb_id'].replace('tt', ''),
            'tvdb' : meta['tvdb_id'],
            'mal' : meta['mal_id'],
            'igdb' : 0,
            'anonymous' : anon,
            'stream' : meta['stream'],
            'sd' : meta['sd'],
            'keywords' : meta['keywords'],
            'personal_release' : int(meta.get('personalrelease', False)),
            'internal' : 0,
            'featured' : 0,
            'free' : 0,
            'doubleup' : 0,
            'sticky' : 0,
        }
        # Internal
        if self.config['TRACKERS'][self.tracker].get('internal', False) == True:
            if meta['tag'] != "" and (meta['tag'][1:] in self.config['TRACKERS'][self.tracker].get('internal_groups', [])):
                data['internal'] = 1
                
        if region_id != 0:
            data['region_id'] = region_id
        if distributor_id != 0:
            data['distributor_id'] = distributor_id
        if meta.get('category') == "TV":
            data['season_number'] = meta.get('season_int', '0')
            data['episode_number'] = meta.get('episode_int', '0')
        headers = {
            'User-Agent': f'Upload Assistant/ CvT Edition ({platform.system()} {platform.release()})'
        }
        params = {
            'api_token' : self.config['TRACKERS'][self.tracker]['api_key'].strip()
        }
        
        if meta['debug'] == False:
            response = requests.post(url=self.upload_url, files=files, data=data, headers=headers, params=params)
            try:
                console.print(response.json())
            except:
                console.print("It may have uploaded, go check")
                return 
        else:
            console.print(f"[cyan]Request Data:")
            console.print(data)
        open_torrent.close()

    def get_language_tag(self, meta):
        audio_lang = []
        if 'mediainfo' in meta:
            for x in meta["mediainfo"]["media"]["track"]:
                if x["@type"] == "Audio":
                    commentary_found = 'Title' in x and ('comment' in x['Title'].lower() or 'review' in x['Title'].lower())
                    if not commentary_found and 'Language_String3' in x:
                        audio_lang.append(x.get('Language_String3'))
            audio_lang = list(dict.fromkeys(audio_lang))  # Remove dupes + keep order
        if not audio_lang:
            audio_lang.append('???')
        lang_tag = f"[{' '.join(lang.upper() for lang in audio_lang)}]"
        sub_lang = [x.get('Language_String3') for x in meta["mediainfo"]["media"]["track"] if x["@type"] == "Text"]
        if not sub_lang:
            sub_lang_tag = "[No Subs]"
        else:
            sub_lang = list(dict.fromkeys(sub_lang))  # Remove dupes + keep order
            if 'spa' in sub_lang:
                if len(sub_lang) > 1:
                    sub_lang_tag = "[Subs SPA+]"
                else:
                    sub_lang_tag = "[Subs SPA]"
            else:
                if sub_lang[0] is None:
                    sub_lang_tag = "[Subs ???]"
                else:
                    if len(sub_lang) > 1:
                        sub_lang_tag = f"[Subs {sub_lang[0].upper()}+]"
                    else:
                        sub_lang_tag = f"[Subs {sub_lang[0].upper()}]"


        return lang_tag+" "+sub_lang_tag


    def get_basename(self, meta):
        path = next(iter(meta['filelist']), meta['path'])
        return os.path.basename(path)
   
    async def get_name(self, meta):
        # Have to agree with whoever made HUNO's script
        # was easier to rebuild name with Prep.get_name() and mofidy 
        # than to attempt to edit the name thereafter - thanks for the tip

        basename = self.get_basename(meta)
        type = meta.get('type', "")
        title = meta.get('title',"")
        alt_title = meta.get('aka', "")
        year = meta.get('year', "")
        resolution = meta.get('resolution', "")
        if resolution == "OTHER":
            resolution = ""
        audio = meta.get('audio', "")
        lang_tag = self.get_language_tag(meta)
        service = meta.get('service', "")
        season = meta.get('season', "")
        episode = meta.get('episode', "")
        part = meta.get('part', "")
        repack = meta.get('repack', "")
        three_d = meta.get('3D', "")
        tag = meta.get('tag', "")
        if tag == "":
            tag = "- NOGRP"
        source = meta.get('source', "")
        uhd = meta.get('uhd', "")
        hdr = meta.get('hdr', "")
        episode_title = meta.get('episode_title', '')
        if meta.get('is_disc', "") == "BDMV": #Disk
            video_codec = meta.get('video_codec', "")
            region = meta.get('region', "")
        elif meta.get('is_disc', "") == "DVD":
            region = meta.get('region', "")
            dvd_size = meta.get('dvd_size', "")
        else:
            video_codec = meta.get('video_codec', "")
            video_encode = meta.get('video_encode', video_codec)
        edition = meta.get('edition', "")

        if meta['category'] == "TV":
            try:
                year = meta['year']
                if not year: 
                    raise ValueError("No TMDB Year Found..trying IMDB")
            except (KeyError, ValueError):
                try:
                    year = meta['imdb_info']['year']
                    if not year:
                        raise ValueError("No IMDB Year Found..")
                except (KeyError, ValueError):
                    year = ""
        if meta.get('no_season', False) == True:
            season = ''
        if meta.get('no_year', False) == True:
            year = ''
        if meta.get('no_aka', False) == True:
            alt_title = ''
        if meta['debug']:
            console.log("[cyan]get_name cat/type")
            console.log(f"CATEGORY: {meta['category']}")
            console.log(f"TYPE: {meta['type']}")
            console.log("[cyan]get_name meta:")
            console.log(meta)

        #YAY NAMING FUN
        if meta['category'] == "MOVIE": #MOVIE SPECIFIC
            if type == "DISC": #Disk
                if meta['is_disc'] == 'BDMV':
                    name = f"{title} [{alt_title}] ({year}) {three_d} [{edition} {repack} {resolution} {region} {uhd} {source} {hdr} {video_codec} {audio}{tag}] {lang_tag}"
                    potential_missing = ['edition', 'region', 'distributor']
                elif meta['is_disc'] == 'DVD': 
                    name = f"{title} {alt_title} ({year}) [{edition} {repack} {source} {dvd_size} {audio}{tag}] {lang_tag}"
                    potential_missing = ['edition', 'distributor']
                elif meta['is_disc'] == 'HDDVD':
                    name = f"{title} {alt_title} ({year}) [{edition} {repack} {resolution} {source} {video_codec}] {audio}{tag}] {lang_tag}"
                    potential_missing = ['edition', 'region', 'distributor']
            elif type == "REMUX" and source in ("BluRay", "HDDVD"): #BluRay/HDDVD Remux
                name = f"{title} {alt_title} ({year}) {three_d} [{edition} {repack} {resolution} {uhd} {source} REMUX {hdr} {video_codec} {audio}{tag}] {lang_tag}" 
                potential_missing = ['edition', 'description']
            elif type == "REMUX" and source in ("PAL DVD", "NTSC DVD", "DVD"): #DVD Remux
                name = f"{title} {alt_title} ({year}) [{edition} {repack} {source} REMUX  {audio}{tag}] {lang_tag}" 
                potential_missing = ['edition', 'description']
            elif type == "ENCODE": #Encode
                name = f"{title} {alt_title} ({year}) [{edition} {repack} {resolution} {uhd} {source} {audio} {hdr} {video_encode}{tag}] {lang_tag}"  
                potential_missing = ['edition', 'description']
            elif type == "WEBDL": #WEB-DL
                name = f"{title} {alt_title} ({year}) [{edition} {repack} {resolution} {uhd} {service} WEB-DL {audio} {hdr} {video_encode}{tag}] {lang_tag}"
                potential_missing = ['edition', 'service']
            elif type == "WEBRIP": #WEBRip
                name = f"{title} {alt_title} ({year}) [{edition} {repack} {resolution} {uhd} {service} WEBRip {audio} {hdr} {video_encode}{tag}] {lang_tag}"
                potential_missing = ['edition', 'service']
            elif type == "HDTV": #HDTV
                name = f"{title} {alt_title} ({year}) [{edition} {repack} {resolution} {source} {audio} {video_encode}{tag}] {lang_tag}"
                potential_missing = []
        elif meta['category'] == "TV": #TV SPECIFIC
            if type == "DISC": #Disk
                if meta['is_disc'] == 'BDMV':
                    name = f"{title} ({year}) {alt_title} {season}{episode} {three_d} [{edition} {repack} {resolution} {region} {uhd} {source} {hdr} {video_codec} {audio}{tag}] {lang_tag}"
                    potential_missing = ['edition', 'region', 'distributor']
                if meta['is_disc'] == 'DVD':
                    name = f"{title} {alt_title} {season}{episode} {three_d} [{edition} {repack} {source} {dvd_size} {audio}{tag}] {lang_tag}"
                    potential_missing = ['edition', 'distributor']
                elif meta['is_disc'] == 'HDDVD':
                    name = f"{title} {alt_title} ({year}) [{edition} {repack} {resolution} {source} {video_codec} {audio}{tag}] {lang_tag}"
                    potential_missing = ['edition', 'region', 'distributor']
            elif type == "REMUX" and source in ("BluRay", "HDDVD"): #BluRay Remux
                name = f"{title} ({year}) {alt_title} {season}{episode} {episode_title} {part} [{three_d} {edition} {repack} {resolution} {uhd} {source} REMUX {hdr} {video_codec} {audio}{tag}] {lang_tag}" #SOURCE
                potential_missing = ['edition', 'description']
            elif type == "REMUX" and source in ("PAL DVD", "NTSC DVD"): #DVD Remux
                name = f"{title} ({year}) {alt_title} {season}{episode} {episode_title} {part} [{edition} {repack} {source} REMUX {audio}{tag}] {lang_tag}" #SOURCE
                potential_missing = ['edition', 'description']
            elif type == "ENCODE": #Encode
                name = f"{title} ({year}) {alt_title} {season}{episode} {episode_title} {part} [{edition} {repack} {resolution} {uhd} {source} {audio} {hdr} {video_encode}{tag}] {lang_tag}" #SOURCE
                potential_missing = ['edition', 'description']
            elif type == "WEBDL": #WEB-DL
                name = f"{title} ({year}) {alt_title} {season}{episode} {episode_title} {part} [{edition} {repack} {resolution} {uhd} {service} WEB-DL {audio} {hdr} {video_encode}{tag}] {lang_tag}"
                potential_missing = ['edition', 'service']
            elif type == "WEBRIP": #WEBRip
                name = f"{title} ({year}) {alt_title} {season}{episode} {episode_title} {part} [{edition} {repack} {resolution} {uhd} {service} WEBRip {audio} {hdr} {video_encode}{tag}] {lang_tag}"
                potential_missing = ['edition', 'service']
            elif type == "HDTV": #HDTV
                name = f"{title} ({year}) {alt_title} {season}{episode} {episode_title} {part} [{edition} {repack} {resolution} {source} {audio} {video_encode}{tag}] {lang_tag}"
                potential_missing = []

        parts = name.split()
        if '[' in parts:        
            bracket_index = parts.index('[')
            sq_bracket = next((i for i, part in enumerate(parts[bracket_index+1:]) if part.strip()), None)
            if sq_bracket is not None:
                name = ' '.join(parts[:bracket_index+1]) + ' '.join(parts[bracket_index+1:])
        
        return ' '.join(name.split())

    async def search_existing(self, meta):
        dupes = []
        console.print("[yellow]Searching for existing torrents on site...")
        params = {
            'api_token' : self.config['TRACKERS'][self.tracker]['api_key'].strip(),
            'tmdbId' : meta['tmdb'],
            'categories[]' : await self.get_cat_id(meta['category']),
            'types[]' : await self.get_type_id(meta['type']),
            'resolutions[]' : await self.get_res_id(meta['resolution']),
            'name' : ""
        }
        if meta.get('edition', "") != "":
            params['name'] = params['name'] + f" {meta['edition']}"
        try:
            response = requests.get(url=self.search_url, params=params)
            response = response.json()
            for each in response['data']:
                result = [each][0]['attributes']['name']
                # difference = SequenceMatcher(None, meta['clean_name'], result).ratio()
                # if difference >= 0.05:
                dupes.append(result)
        except:
            console.print('[bold red]Unable to search for existing torrents on site. Either the site is down or your API key is incorrect')
            await asyncio.sleep(5)

        return dupes
