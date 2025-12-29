#!/usr/bin/env python3
"""
Script d'ajout de sources pour Radar
Plus de 200 sources dans l'industrie musicale
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.source import SourceConfig
from app.db.models.opportunity import SourceType

# Sources organisées par catégorie
SOURCES = [
    # ========================================
    # MÉDIAS MUSIQUE FRANCE
    # ========================================
    {"name": "Les Inrockuptibles", "type": "RSS", "url": "https://www.lesinrocks.com/feed/", "category": "media_fr"},
    {"name": "Télérama Musique", "type": "RSS", "url": "https://www.telerama.fr/rss/musique.xml", "category": "media_fr"},
    {"name": "Libération Musique", "type": "RSS", "url": "https://www.liberation.fr/rss/musique/", "category": "media_fr"},
    {"name": "Le Monde Musique", "type": "RSS", "url": "https://www.lemonde.fr/musiques/rss_full.xml", "category": "media_fr"},
    {"name": "France Inter Culture", "type": "RSS", "url": "https://www.franceinter.fr/rss/culture.xml", "category": "media_fr"},
    {"name": "France Culture Musique", "type": "RSS", "url": "https://www.franceculture.fr/rss/musique.xml", "category": "media_fr"},
    {"name": "Tsugi", "type": "RSS", "url": "https://www.tsugi.fr/feed/", "category": "media_fr"},
    {"name": "Trax Magazine", "type": "RSS", "url": "https://www.traxmag.com/feed/", "category": "media_fr"},
    {"name": "Mouv'", "type": "RSS", "url": "https://www.mouv.fr/rss/musique.xml", "category": "media_fr"},
    {"name": "Nova", "type": "RSS", "url": "https://www.nova.fr/feed/", "category": "media_fr"},
    {"name": "FIP", "type": "RSS", "url": "https://www.fip.fr/rss/actualites.xml", "category": "media_fr"},
    {"name": "Music Actu", "type": "RSS", "url": "https://www.music-actu.com/feed/", "category": "media_fr"},
    {"name": "Gonzai", "type": "RSS", "url": "https://gonzai.com/feed/", "category": "media_fr"},
    {"name": "Pan European Recording", "type": "RSS", "url": "https://pan-european-recording.com/feed/", "category": "media_fr"},
    {"name": "Brain Magazine", "type": "RSS", "url": "https://www.brain-magazine.fr/feed", "category": "media_fr"},
    
    # ========================================
    # MÉDIAS MUSIQUE INTERNATIONAL
    # ========================================
    {"name": "Pitchfork", "type": "RSS", "url": "https://pitchfork.com/rss/news/", "category": "media_int"},
    {"name": "Pitchfork Reviews", "type": "RSS", "url": "https://pitchfork.com/rss/reviews/albums/", "category": "media_int"},
    {"name": "NME", "type": "RSS", "url": "https://www.nme.com/music/feed", "category": "media_int"},
    {"name": "Rolling Stone", "type": "RSS", "url": "https://www.rollingstone.com/music/feed/", "category": "media_int"},
    {"name": "Billboard", "type": "RSS", "url": "https://www.billboard.com/feed/", "category": "media_int"},
    {"name": "Consequence", "type": "RSS", "url": "https://consequence.net/feed/", "category": "media_int"},
    {"name": "Stereogum", "type": "RSS", "url": "https://www.stereogum.com/feed/", "category": "media_int"},
    {"name": "The Line of Best Fit", "type": "RSS", "url": "https://www.thelineofbestfit.com/feed", "category": "media_int"},
    {"name": "DIY Magazine", "type": "RSS", "url": "https://diymag.com/feed", "category": "media_int"},
    {"name": "Clash Magazine", "type": "RSS", "url": "https://www.clashmusic.com/feed/", "category": "media_int"},
    {"name": "The Quietus", "type": "RSS", "url": "https://thequietus.com/feed", "category": "media_int"},
    {"name": "Loud and Quiet", "type": "RSS", "url": "https://www.loudandquiet.com/feed/", "category": "media_int"},
    {"name": "The Fader", "type": "RSS", "url": "https://www.thefader.com/rss.xml", "category": "media_int"},
    {"name": "Complex Music", "type": "RSS", "url": "https://www.complex.com/music/rss", "category": "media_int"},
    {"name": "Hypebeast Music", "type": "RSS", "url": "https://hypebeast.com/music/feed", "category": "media_int"},
    {"name": "Highsnobiety Music", "type": "RSS", "url": "https://www.highsnobiety.com/music/feed/", "category": "media_int"},
    {"name": "Resident Advisor News", "type": "RSS", "url": "https://ra.co/xml/news.xml", "category": "media_int"},
    {"name": "Mixmag", "type": "RSS", "url": "https://mixmag.net/feed", "category": "media_int"},
    {"name": "DJ Mag", "type": "RSS", "url": "https://djmag.com/feed", "category": "media_int"},
    {"name": "Electronic Beats", "type": "RSS", "url": "https://www.electronicbeats.net/feed/", "category": "media_int"},
    {"name": "XLR8R", "type": "RSS", "url": "https://xlr8r.com/feed/", "category": "media_int"},
    {"name": "Bandcamp Daily", "type": "RSS", "url": "https://daily.bandcamp.com/feed", "category": "media_int"},
    
    # ========================================
    # INDUSTRIE MUSICALE / BUSINESS
    # ========================================
    {"name": "Music Business Worldwide", "type": "RSS", "url": "https://www.musicbusinessworldwide.com/feed/", "category": "industry"},
    {"name": "Hypebot", "type": "RSS", "url": "https://www.hypebot.com/feed/", "category": "industry"},
    {"name": "Music Ally", "type": "RSS", "url": "https://musically.com/feed/", "category": "industry"},
    {"name": "Digital Music News", "type": "RSS", "url": "https://www.digitalmusicnews.com/feed/", "category": "industry"},
    {"name": "Music Week", "type": "RSS", "url": "https://www.musicweek.com/rss/musicweek/news", "category": "industry"},
    {"name": "Record of the Day", "type": "RSS", "url": "https://www.recordoftheday.com/feed", "category": "industry"},
    {"name": "Complete Music Update", "type": "RSS", "url": "https://completemusicupdate.com/feed/", "category": "industry"},
    {"name": "IRMA Actus", "type": "RSS", "url": "https://www.irma.asso.fr/spip.php?page=backend", "category": "industry"},
    {"name": "CNM Actualités", "type": "RSS", "url": "https://cnm.fr/feed/", "category": "industry"},
    {"name": "SNEP Actualités", "type": "RSS", "url": "https://snepmusique.com/feed/", "category": "industry"},
    {"name": "UPFI News", "type": "RSS", "url": "https://www.upfi.fr/feed/", "category": "industry"},
    {"name": "Audiofanzine Pro", "type": "RSS", "url": "https://fr.audiofanzine.com/rss/news.xml", "category": "industry"},
    
    # ========================================
    # FESTIVALS & ÉVÉNEMENTS
    # ========================================
    {"name": "Festival Eurockéennes", "type": "RSS", "url": "https://www.eurockeennes.fr/feed/", "category": "festivals"},
    {"name": "Hellfest", "type": "RSS", "url": "https://www.hellfest.fr/feed/", "category": "festivals"},
    {"name": "Printemps de Bourges", "type": "RSS", "url": "https://www.printemps-bourges.com/feed/", "category": "festivals"},
    {"name": "Francofolies", "type": "RSS", "url": "https://www.francofolies.fr/feed/", "category": "festivals"},
    {"name": "Vieilles Charrues", "type": "RSS", "url": "https://www.vieillescharrues.asso.fr/feed/", "category": "festivals"},
    {"name": "Solidays", "type": "RSS", "url": "https://www.solidays.org/feed/", "category": "festivals"},
    {"name": "Rock en Seine", "type": "RSS", "url": "https://www.rockenseine.com/feed/", "category": "festivals"},
    {"name": "Main Square Festival", "type": "RSS", "url": "https://www.mainsquarefestival.fr/feed/", "category": "festivals"},
    {"name": "Garorock", "type": "RSS", "url": "https://www.garorock.com/feed/", "category": "festivals"},
    {"name": "Musilac", "type": "RSS", "url": "https://www.musilac.com/feed/", "category": "festivals"},
    {"name": "Nuits Sonores", "type": "RSS", "url": "https://www.nuits-sonores.com/feed/", "category": "festivals"},
    {"name": "Pitchfork Paris", "type": "RSS", "url": "https://pitchforkmusicfestival.fr/feed/", "category": "festivals"},
    {"name": "We Love Green", "type": "RSS", "url": "https://www.welovegreen.fr/feed/", "category": "festivals"},
    {"name": "Transmusicales", "type": "RSS", "url": "https://www.lestrans.com/feed/", "category": "festivals"},
    {"name": "MaMA Festival", "type": "RSS", "url": "https://www.mamafestival.com/feed/", "category": "festivals"},
    {"name": "Bise Festival", "type": "RSS", "url": "https://www.bisefestival.com/feed/", "category": "festivals"},
    {"name": "Cabaret Vert", "type": "RSS", "url": "https://www.cabaretvert.com/feed/", "category": "festivals"},
    {"name": "Papillons de Nuit", "type": "RSS", "url": "https://www.papillonsdenuit.com/feed/", "category": "festivals"},
    {"name": "Sziget Festival", "type": "RSS", "url": "https://szigetfestival.com/feed/", "category": "festivals"},
    {"name": "Primavera Sound", "type": "RSS", "url": "https://www.primaverasound.com/feed/", "category": "festivals"},
    {"name": "Glastonbury", "type": "RSS", "url": "https://www.glastonburyfestivals.co.uk/feed/", "category": "festivals"},
    {"name": "Coachella", "type": "RSS", "url": "https://www.coachella.com/feed/", "category": "festivals"},
    {"name": "Tomorrowland", "type": "RSS", "url": "https://www.tomorrowland.com/feed/", "category": "festivals"},
    {"name": "Sonar Festival", "type": "RSS", "url": "https://sonar.es/feed/", "category": "festivals"},
    {"name": "ADE Amsterdam", "type": "RSS", "url": "https://www.amsterdam-dance-event.nl/feed/", "category": "festivals"},
    
    # ========================================
    # SALLES DE CONCERT FRANCE
    # ========================================
    {"name": "Olympia Paris", "type": "RSS", "url": "https://www.olympiahall.com/feed/", "category": "venues"},
    {"name": "Zénith Paris", "type": "RSS", "url": "https://www.zenith-paris.com/feed/", "category": "venues"},
    {"name": "Accor Arena", "type": "RSS", "url": "https://www.accorarena.com/feed/", "category": "venues"},
    {"name": "La Cigale", "type": "RSS", "url": "https://www.lacigale.fr/feed/", "category": "venues"},
    {"name": "Le Bataclan", "type": "RSS", "url": "https://www.bataclan.fr/feed/", "category": "venues"},
    {"name": "L'Élysée Montmartre", "type": "RSS", "url": "https://www.elysee-montmartre.com/feed/", "category": "venues"},
    {"name": "La Maroquinerie", "type": "RSS", "url": "https://www.lamaroquinerie.fr/feed/", "category": "venues"},
    {"name": "Le Trabendo", "type": "RSS", "url": "https://www.letrabendo.net/feed/", "category": "venues"},
    {"name": "La Gaîté Lyrique", "type": "RSS", "url": "https://gaite-lyrique.net/feed/", "category": "venues"},
    {"name": "Philharmonie de Paris", "type": "RSS", "url": "https://philharmoniedeparis.fr/feed/", "category": "venues"},
    {"name": "Le Transbordeur Lyon", "type": "RSS", "url": "https://www.transbordeur.fr/feed/", "category": "venues"},
    {"name": "Le Rocher de Palmer", "type": "RSS", "url": "https://lerocherdepalmer.fr/feed/", "category": "venues"},
    {"name": "Stereolux Nantes", "type": "RSS", "url": "https://www.stereolux.org/feed/", "category": "venues"},
    {"name": "La Belle Électrique Grenoble", "type": "RSS", "url": "https://www.la-belle-electrique.com/feed/", "category": "venues"},
    {"name": "L'Aéronef Lille", "type": "RSS", "url": "https://www.aeronef.fr/feed/", "category": "venues"},
    {"name": "Le Krakatoa Bordeaux", "type": "RSS", "url": "https://www.krakatoa.org/feed/", "category": "venues"},
    {"name": "Le Bikini Toulouse", "type": "RSS", "url": "https://www.lebikini.com/feed/", "category": "venues"},
    {"name": "La Laiterie Strasbourg", "type": "RSS", "url": "https://www.artefact.org/feed/", "category": "venues"},
    {"name": "Le Cargö Caen", "type": "RSS", "url": "https://www.lecargo.fr/feed/", "category": "venues"},
    {"name": "La Coopérative de Mai", "type": "RSS", "url": "https://www.lacoope.org/feed/", "category": "venues"},
    
    # ========================================
    # LABELS INDÉPENDANTS
    # ========================================
    {"name": "Because Music", "type": "RSS", "url": "https://www.because.tv/feed/", "category": "labels"},
    {"name": "Wagram Music", "type": "RSS", "url": "https://www.wagrammusic.com/feed/", "category": "labels"},
    {"name": "Naïve Records", "type": "RSS", "url": "https://www.naive.fr/feed/", "category": "labels"},
    {"name": "Tricatel", "type": "RSS", "url": "https://tricatel.com/feed/", "category": "labels"},
    {"name": "Ed Banger Records", "type": "RSS", "url": "https://www.edbangerrecords.com/feed/", "category": "labels"},
    {"name": "Bromance Records", "type": "RSS", "url": "https://bromancerecords.com/feed/", "category": "labels"},
    {"name": "Roche Musique", "type": "RSS", "url": "https://www.rfrmusique.com/feed/", "category": "labels"},
    {"name": "Nowadays Records", "type": "RSS", "url": "https://nowadaysrecords.com/feed/", "category": "labels"},
    {"name": "Ninja Tune", "type": "RSS", "url": "https://ninjatune.net/feed", "category": "labels"},
    {"name": "Warp Records", "type": "RSS", "url": "https://warp.net/feed/", "category": "labels"},
    {"name": "4AD", "type": "RSS", "url": "https://4ad.com/feed/", "category": "labels"},
    {"name": "Domino Records", "type": "RSS", "url": "https://www.dominomusic.com/feed/", "category": "labels"},
    {"name": "Rough Trade", "type": "RSS", "url": "https://www.roughtraderecords.com/feed/", "category": "labels"},
    {"name": "XL Recordings", "type": "RSS", "url": "https://xlrecordings.com/feed/", "category": "labels"},
    {"name": "Sub Pop", "type": "RSS", "url": "https://www.subpop.com/feed/", "category": "labels"},
    {"name": "Secretly Canadian", "type": "RSS", "url": "https://secretlycanadian.com/feed/", "category": "labels"},
    {"name": "Jagjaguwar", "type": "RSS", "url": "https://jagjaguwar.com/feed/", "category": "labels"},
    {"name": "Stones Throw", "type": "RSS", "url": "https://www.stonesthrow.com/feed/", "category": "labels"},
    {"name": "Brainfeeder", "type": "RSS", "url": "https://brainfeedersite.com/feed/", "category": "labels"},
    {"name": "Kompakt", "type": "RSS", "url": "https://kompakt.fm/feed/", "category": "labels"},
    {"name": "Innervisions", "type": "RSS", "url": "https://www.innervisions.de/feed/", "category": "labels"},
    {"name": "Running Back", "type": "RSS", "url": "https://runningback.org/feed/", "category": "labels"},
    {"name": "Beats in Space", "type": "RSS", "url": "https://www.beatsinspace.net/feed/", "category": "labels"},
    
    # ========================================
    # RAP / HIP-HOP FR
    # ========================================
    {"name": "Booska-P", "type": "RSS", "url": "https://www.booska-p.com/feed/", "category": "hiphop_fr"},
    {"name": "Rapelite", "type": "RSS", "url": "https://rapelite.com/feed/", "category": "hiphop_fr"},
    {"name": "Générations", "type": "RSS", "url": "https://generations.fr/feed/", "category": "hiphop_fr"},
    {"name": "L'Abcdr du Son", "type": "RSS", "url": "https://www.abcdrduson.com/feed/", "category": "hiphop_fr"},
    {"name": "Mouv' Rap FR", "type": "RSS", "url": "https://www.mouv.fr/rap-francais/feed/", "category": "hiphop_fr"},
    {"name": "Le Rap en France", "type": "RSS", "url": "https://lerapenfrance.fr/feed/", "category": "hiphop_fr"},
    {"name": "SURL Magazine", "type": "RSS", "url": "https://surlmag.fr/feed/", "category": "hiphop_fr"},
    {"name": "Yard", "type": "RSS", "url": "https://yard.media/feed/", "category": "hiphop_fr"},
    {"name": "Red Bull Music FR", "type": "RSS", "url": "https://www.redbull.com/fr-fr/music/feed", "category": "hiphop_fr"},
    {"name": "Trace Urban", "type": "RSS", "url": "https://trace.tv/feed/", "category": "hiphop_fr"},
    
    # ========================================
    # APPELS À PROJETS / SUBVENTIONS
    # ========================================
    {"name": "CNM Appels à projets", "type": "RSS", "url": "https://cnm.fr/aides/feed/", "category": "funding"},
    {"name": "SACEM Aides", "type": "RSS", "url": "https://www.sacem.fr/feed/", "category": "funding"},
    {"name": "ADAMI Aides", "type": "RSS", "url": "https://www.adami.fr/feed/", "category": "funding"},
    {"name": "SPEDIDAM Aides", "type": "RSS", "url": "https://www.spedidam.fr/feed/", "category": "funding"},
    {"name": "FCM Aides", "type": "RSS", "url": "https://www.fcm.fr/feed/", "category": "funding"},
    {"name": "Culture.gouv.fr Musique", "type": "RSS", "url": "https://www.culture.gouv.fr/rss/musique", "category": "funding"},
    {"name": "Transfo", "type": "RSS", "url": "https://transfo-lemans.fr/feed/", "category": "funding"},
    {"name": "Fair", "type": "RSS", "url": "https://www.lefair.org/feed/", "category": "funding"},
    {"name": "Région Île-de-France Culture", "type": "RSS", "url": "https://www.iledefrance.fr/culture/feed/", "category": "funding"},
    {"name": "Région Occitanie Culture", "type": "RSS", "url": "https://www.laregion.fr/culture/feed/", "category": "funding"},
    {"name": "Région AURA Spectacle", "type": "RSS", "url": "https://www.auvergnerhonealpes.fr/culture/feed/", "category": "funding"},
    {"name": "Creative Europe Music", "type": "RSS", "url": "https://culture.ec.europa.eu/rss/music", "category": "funding"},
    
    # ========================================
    # TREMPLINS & CONCOURS
    # ========================================
    {"name": "Victoires de la Musique", "type": "RSS", "url": "https://www.lesvictoires.com/feed/", "category": "contests"},
    {"name": "Prix Constantin", "type": "RSS", "url": "https://www.prixconstantin.com/feed/", "category": "contests"},
    {"name": "Inouïs du Printemps", "type": "RSS", "url": "https://www.printemps-bourges.com/inouis/feed/", "category": "contests"},
    {"name": "Chorus des Hauts-de-Seine", "type": "RSS", "url": "https://www.chorus.hauts-de-seine.fr/feed/", "category": "contests"},
    {"name": "Buzzcocks", "type": "RSS", "url": "https://buzzcocks.fr/feed/", "category": "contests"},
    {"name": "Pépites", "type": "RSS", "url": "https://lespepites.com/feed/", "category": "contests"},
    {"name": "Talent Adami", "type": "RSS", "url": "https://www.adami.fr/talents/feed/", "category": "contests"},
    
    # ========================================
    # BLOGS & DÉCOUVERTES
    # ========================================
    {"name": "La Blogothèque", "type": "RSS", "url": "https://www.blogotheque.net/feed/", "category": "blogs"},
    {"name": "Colors Berlin", "type": "RSS", "url": "https://www.colorsxstudios.com/feed/", "category": "blogs"},
    {"name": "KEXP", "type": "RSS", "url": "https://www.kexp.org/feed/", "category": "blogs"},
    {"name": "Tiny Desk NPR", "type": "RSS", "url": "https://www.npr.org/rss/rss.php?id=152914736", "category": "blogs"},
    {"name": "Indie Shuffle", "type": "RSS", "url": "https://www.indieshuffle.com/feed/", "category": "blogs"},
    {"name": "The Burning Ear", "type": "RSS", "url": "https://www.theburningear.com/feed/", "category": "blogs"},
    {"name": "Gorilla vs Bear", "type": "RSS", "url": "https://www.gorillavsbear.net/feed/", "category": "blogs"},
    {"name": "Pigeons and Planes", "type": "RSS", "url": "https://www.complex.com/pigeons-and-planes/feed", "category": "blogs"},
    {"name": "Earmilk", "type": "RSS", "url": "https://earmilk.com/feed/", "category": "blogs"},
    {"name": "Hype Machine", "type": "RSS", "url": "https://hypem.com/feed/", "category": "blogs"},
    {"name": "The 405", "type": "RSS", "url": "https://www.thefourohfive.com/feed/", "category": "blogs"},
    {"name": "Gold Flake Paint", "type": "RSS", "url": "https://www.goldflakepaint.co.uk/feed/", "category": "blogs"},
    {"name": "Atwood Magazine", "type": "RSS", "url": "https://atwoodmagazine.com/feed/", "category": "blogs"},
    
    # ========================================
    # RADIO & PODCASTS
    # ========================================
    {"name": "France Inter Pop", "type": "RSS", "url": "https://www.franceinter.fr/emissions/pop-n-co/rss", "category": "radio"},
    {"name": "RTL2 Pop Rock", "type": "RSS", "url": "https://www.rtl2.fr/feed/", "category": "radio"},
    {"name": "OÜI FM", "type": "RSS", "url": "https://www.ouifm.fr/feed/", "category": "radio"},
    {"name": "Le Mouv' Playlist", "type": "RSS", "url": "https://www.mouv.fr/emissions/mouv-inside/feed", "category": "radio"},
    {"name": "FIP Découvertes", "type": "RSS", "url": "https://www.fip.fr/emissions/fip-decouvertes/feed", "category": "radio"},
    {"name": "Radio Meuh", "type": "RSS", "url": "https://www.radiomeuh.com/feed/", "category": "radio"},
    {"name": "Rinse France", "type": "RSS", "url": "https://rinse.fr/feed/", "category": "radio"},
    {"name": "NTS Radio", "type": "RSS", "url": "https://www.nts.live/feed", "category": "radio"},
    {"name": "Boiler Room", "type": "RSS", "url": "https://boilerroom.tv/feed/", "category": "radio"},
    {"name": "LeMellotron", "type": "RSS", "url": "https://www.lemellotron.com/feed/", "category": "radio"},
    
    # ========================================
    # TECH & STREAMING
    # ========================================
    {"name": "Spotify for Artists Blog", "type": "RSS", "url": "https://artists.spotify.com/blog/feed", "category": "tech"},
    {"name": "Apple Music for Artists", "type": "RSS", "url": "https://artists.apple.com/feed/", "category": "tech"},
    {"name": "Deezer for Creators", "type": "RSS", "url": "https://www.deezer-blog.com/feed/", "category": "tech"},
    {"name": "Bandcamp Blog", "type": "RSS", "url": "https://blog.bandcamp.com/feed/", "category": "tech"},
    {"name": "SoundCloud Blog", "type": "RSS", "url": "https://blog.soundcloud.com/feed/", "category": "tech"},
    {"name": "DistroKid Blog", "type": "RSS", "url": "https://news.distrokid.com/feed/", "category": "tech"},
    {"name": "TuneCore Blog", "type": "RSS", "url": "https://www.tunecore.com/blog/feed", "category": "tech"},
    {"name": "CD Baby Blog", "type": "RSS", "url": "https://diymusician.cdbaby.com/feed/", "category": "tech"},
    {"name": "Ari's Take", "type": "RSS", "url": "https://aristake.com/feed/", "category": "tech"},
    
    # ========================================
    # SYNC & PLACEMENTS
    # ========================================
    {"name": "Music Supervisor", "type": "RSS", "url": "https://www.musicsupervisor.com/feed/", "category": "sync"},
    {"name": "Synchtank Blog", "type": "RSS", "url": "https://www.synchtank.com/blog/feed/", "category": "sync"},
    {"name": "Production Music Live", "type": "RSS", "url": "https://www.productionmusiclive.com/feed/", "category": "sync"},
    {"name": "Musicbed Blog", "type": "RSS", "url": "https://www.musicbed.com/blog/feed/", "category": "sync"},
    {"name": "Artlist Blog", "type": "RSS", "url": "https://artlist.io/blog/feed/", "category": "sync"},
    {"name": "Epidemic Sound Blog", "type": "RSS", "url": "https://www.epidemicsound.com/blog/feed/", "category": "sync"},
    
    # ========================================
    # PRODUCTION & STUDIO
    # ========================================
    {"name": "Sound on Sound", "type": "RSS", "url": "https://www.soundonsound.com/rss/news", "category": "production"},
    {"name": "MusicRadar", "type": "RSS", "url": "https://www.musicradar.com/rss", "category": "production"},
    {"name": "Attack Magazine", "type": "RSS", "url": "https://www.attackmagazine.com/feed/", "category": "production"},
    {"name": "Reverb Machine", "type": "RSS", "url": "https://reverbmachine.com/feed/", "category": "production"},
    {"name": "Pro Tools Expert", "type": "RSS", "url": "https://www.pro-tools-expert.com/feed/", "category": "production"},
    {"name": "Tape Op", "type": "RSS", "url": "https://tapeop.com/feed/", "category": "production"},
    {"name": "Recording Magazine", "type": "RSS", "url": "https://www.recordingmag.com/feed/", "category": "production"},
    {"name": "Gearslutz", "type": "RSS", "url": "https://gearspace.com/board/external.php?type=RSS2", "category": "production"},
    
    # ========================================
    # BOOKING & TOURNÉES
    # ========================================
    {"name": "Pollstar", "type": "RSS", "url": "https://www.pollstar.com/rss/", "category": "booking"},
    {"name": "IQ Magazine", "type": "RSS", "url": "https://www.iq-mag.net/feed/", "category": "booking"},
    {"name": "Live Nation Blog", "type": "RSS", "url": "https://www.livenation.fr/feed/", "category": "booking"},
    {"name": "Songkick Blog", "type": "RSS", "url": "https://blog.songkick.com/feed/", "category": "booking"},
    {"name": "Bandsintown for Artists", "type": "RSS", "url": "https://artists.bandsintown.com/feed/", "category": "booking"},
    
    # ========================================
    # JAZZ & CLASSIQUE
    # ========================================
    {"name": "Jazz Magazine", "type": "RSS", "url": "https://www.jazzmagazine.com/feed/", "category": "jazz"},
    {"name": "Citizen Jazz", "type": "RSS", "url": "https://www.citizenjazz.com/spip.php?page=backend", "category": "jazz"},
    {"name": "Jazz News", "type": "RSS", "url": "https://www.jazznews.fr/feed/", "category": "jazz"},
    {"name": "All About Jazz", "type": "RSS", "url": "https://www.allaboutjazz.com/rss/feed.xml", "category": "jazz"},
    {"name": "Classica", "type": "RSS", "url": "https://www.classica.fr/feed/", "category": "jazz"},
    {"name": "Diapason", "type": "RSS", "url": "https://www.diapasonmag.fr/feed/", "category": "jazz"},
    {"name": "ResMusica", "type": "RSS", "url": "https://www.resmusica.com/feed/", "category": "jazz"},
    
    # ========================================
    # METAL & ROCK
    # ========================================
    {"name": "Metal France", "type": "RSS", "url": "https://www.metalfrance.net/feed/", "category": "metal"},
    {"name": "Metalorgie", "type": "RSS", "url": "https://www.metalorgie.com/feed/", "category": "metal"},
    {"name": "Versus Magazine", "type": "RSS", "url": "https://www.yourwebsite.fr/feed/", "category": "metal"},
    {"name": "Bloody Blackbird", "type": "RSS", "url": "https://www.bloodyblackbird.com/feed/", "category": "metal"},
    {"name": "Metal Hammer", "type": "RSS", "url": "https://www.metalhammer.de/feed/", "category": "metal"},
    {"name": "Kerrang!", "type": "RSS", "url": "https://www.kerrang.com/feed/", "category": "metal"},
    {"name": "Revolver Magazine", "type": "RSS", "url": "https://www.revolvermag.com/rss.xml", "category": "metal"},
    {"name": "Blabbermouth", "type": "RSS", "url": "https://www.blabbermouth.net/feed/", "category": "metal"},
    {"name": "Metal Injection", "type": "RSS", "url": "https://metalinjection.net/feed", "category": "metal"},
    {"name": "Loudwire", "type": "RSS", "url": "https://loudwire.com/feed/", "category": "metal"},
]


def add_sources():
    """Ajoute toutes les sources à la base de données"""
    db: Session = SessionLocal()
    
    added = 0
    skipped = 0
    errors = 0
    
    try:
        for source_data in SOURCES:
            try:
                # Vérifier si la source existe déjà
                existing = db.query(SourceConfig).filter(
                    SourceConfig.url == source_data["url"]
                ).first()
                
                if existing:
                    skipped += 1
                    print(f"⏭️  Skip (existe): {source_data['name']}")
                    continue
                
                # Créer la source
                source = SourceConfig(
                    name=source_data["name"],
                    source_type=SourceType(source_data["type"]),
                    url=source_data["url"],
                    description=source_data.get("category", "other"),
                    is_active=True
                )
                
                db.add(source)
                db.commit()
                added += 1
                print(f"✅ Ajouté: {source_data['name']}")
                
            except Exception as e:
                db.rollback()
                errors += 1
                print(f"❌ Erreur ({source_data['name']}): {e}")
                continue
        
        print("\n" + "="*50)
        print(f"📊 RÉSUMÉ:")
        print(f"   ✅ Ajoutées: {added}")
        print(f"   ⏭️  Skippées: {skipped}")
        print(f"   ❌ Erreurs: {errors}")
        print(f"   📁 Total sources: {db.query(SourceConfig).count()}")
        print("="*50)
        
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Ajout des sources Radar...")
    print(f"📋 {len(SOURCES)} sources à traiter\n")
    add_sources()
