# -*- coding: utf8 -*-
###
# Copyright (c) 2010, Valentin Lorentz
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import re
import supybot.world as world
import supybot.ircmsgs as ircmsgs
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

class SpellChecker:
    def __init__(self, text, level):
        # 0 : pas de filtrage ;
        # 1 : filtre le langage SMS
        # 2 : filtre les erreurs de pluriel ;
        # 3 : filtre les fautes de conjugaison courantes ;
        # 4 : filtre les fautes d'orthographe courantes ;
        # 5 : filtre les abbréviations ("t'as" au lieu de "tu as")
        self._text = text
        self._errors = []
        if level >= 1:
            self._checking = 'SMS'
            self.checkSMS()
        if level >= 2:
            self._checking = 'pluriel'
            self.checkPlural()
        if level >= 3:
            self._checking = 'conjugaison'
            self.checkConjugaison()
        if level >= 4:
            self._checking = 'orthographe'
            self.checkSpelling()
        if level >= 5:
            self._checking = 'abbréviation'
            self.checkAbbreviation()
        if level >= 6:
            self._checking = 'typographie'
            self.checkTypographic()
        if level >= 7:
            self._checking = 'lol'
            self.checkLol()
    
    def _raise(self, message):
        self._errors.append('[%s] %s' % (self._checking, message))
    
    def _detect(self, mode, correct, mask, displayedMask=None, wizard=' '):
        if displayedMask is None:
            displayedMask = mask
        raise_ = False
        text = '%s%s%s' % (wizard, self._text, wizard)
        if mode == 'single' and re.match('.*\W%s\W.*' % mask, text,
                                         re.IGNORECASE) is not None:
            raise_ = True
        elif mode == 'regexp' and re.match('.*%s.*' % mask, text):
            raise_ = True
        
        if raise_:
            if self._checking == 'conjugaison' or \
            self._checking == 'typographie':
                self._raise(correct)
            else:
                if correct.__class__ == list:
                    correct = '`%s`' % '`, ou `'.join(correct)
                else:
                    correct = '`%s`' % correct
                    
                if displayedMask.__class__ == list:
                    displayedMask = '`%s`' % '` ou `'.join(displayedMask)
                else:
                    displayedMask = '`%s`' % displayedMask
                self._raise('On ne dit pas %s mais %s' %
                           (displayedMask, correct))

    def checkSMS(self):
        self._detect(mode='single', correct='tout', mask='tt')
        self._detect(mode='single', correct='tous', mask='ts')
        self._detect(mode='single', correct='toute', mask='tte')
        self._detect(mode='single', correct='toutes', mask='ttes')
        self._detect(mode='single', correct="c'était", mask='ct')
        self._detect(mode='single', correct="vais", mask='v')
        self._detect(mode='single', correct=["aime", "aimes", "aiment"],
                     mask='m')
        self._detect(mode='single', correct=['eu', 'eut'], mask='u')
        self._detect(mode='regexp', correct="c'est", 
                     mask="(?<!(du|Du|le|Le|en|En)) C (?<!c')",
                     displayedMask='C')

    def checkPlural(self):
        pass
    def checkConjugaison(self):
        self._detect(mode='regexp', correct="t'as oublié un `ne` ou un `n'`",
                     mask="(je|tu|on|il|elle|nous|vous|ils|elles) [^' ]+ pas")
        self._detect(mode='regexp', correct="t'as oublié un `ne` ou un `n'`",
                     mask="j'[^' ]+ pas")
        firstPerson = 'un verbe à la première personne ne finit pas par un `t`'
        notAS = 'ce verbe ne devrait pas se finir par un `s` à cette personne.'
        self._detect(mode='regexp', correct=firstPerson, mask="j'[^ ]*t")
        self._detect(mode='regexp', correct=firstPerson,mask="je( ne)? [^ ]*t")
        self._detect(mode='regexp', correct=notAS,
                     mask="(il|elle|on)( ne | n'| )[^ ]*s\W")
    def checkSpelling(self):
        self._detect(mode='regexp', correct='quelle', mask='quel [^ ]+ la',
                     displayedMask='quel')
        self._detect(mode='regexp', correct='quel', mask='quelle [^ ]+ le',
                     displayedMask='quelle')
        self._detect(mode='regexp', correct=['quels', 'quelles'],
                     mask='quel [^ ]+ les',
                     displayedMask='quel')
        self._detect(mode='regexp', correct=['quels', 'quelles'],
                     mask='quelle [^ ]+ les',
                     displayedMask='quelle')
        self._detect(mode='regexp',
                     correct=['quel', 'quels', 'quelle', 'quelles'],
                     mask='kel(le)?s?',
                     displayedMask=['kel', 'kels', 'kelle', 'kelles'])
    def checkAbbreviation(self):
        pass
    def checkLol(self):
        self._detect(mode='regexp', correct='mdr', mask='[Ll1][oO0 ]+[lL1]',
                     displayedMask='lol')
    def checkTypographic(self):
        self._detect(mode='regexp',
                     correct="Un caractère de ponctuation double est toujours "
                     "précédé d'un espace",
                     mask="[^ _][:!?;]", wizard='_')
        self._detect(mode='regexp',
                     correct="Un caractère de ponctuation simple est toujours "
                     "suivi d'un espace",
                     mask="[:!?;][^ _]", wizard='_')
        self._detect(mode='regexp',
                     correct="Un caractère de ponctuation simple n'est jamais "
                     "précédé d'un espace",
                     mask=" ,", wizard='_')
        self._detect(mode='regexp',
                     correct="Un caractère de ponctuation simple est toujours "
                     "suivi d'un espace",
                     mask=",[^ _]", wizard='_')
    
    def getErrors(self):
        return self._errors

class GoodFrench(callbacks.Plugin):
    def detect(self, irc, msg, args, text):
        """<texte>
        
        Cherche des fautes dans le <texte>, en fonction de la valeur locale de
        supybot.plugins.GoodFrench.level."""
        checker = SpellChecker(text, self.registryValue('level', msg.channel))
        errors = checker.getErrors()
        if len(errors) == 0:
            irc.reply('La phrase semble correcte')
        elif len(errors) == 1:
            irc.reply('Il semble y avoir une erreur : %s' % errors[0])
        else:
            irc.reply('Il semble y avoir des erreurs : %s' %
                      ' | '.join(errors))
    def doPrivmsg(self, irc, msg):
        if world.testing: # FIXME
            return
        channel = msg.args[0]
        prefix = msg.prefix
        nick = prefix.split('!')[0]
        text = msg.args[1]
        
        print self.registryValue('level', channel)
        checker = SpellChecker(text, self.registryValue('level', channel))
        errors = checker.getErrors()
        print errors
        if len(errors) == 0:
            return
        elif len(errors) == 1:
            reason = 'Erreur : %s' % errors[0]
        else:
            reason = 'Erreurs : %s' % ' | '.join(errors)
        print 'titi'
        msg = ircmsgs.kick(channel, nick, reason)
        print 'toto'
        irc.queueMsg(msg)
    
    detect = wrap(detect, ['text'])


Class = GoodFrench


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79: