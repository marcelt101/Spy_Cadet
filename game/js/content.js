/* Everything the player reads, in one place so it can be checked by a historian and translated.
   Campaign 1: The Midway Code, Pacific 1942, played at Station HYPO, the US Navy codebreaking office at Pearl Harbor.
   Words in messages are code-book entries: a word or a short phrase has one 5-digit code group. */
(function () {
const SC = window.SC = window.SC || {};

SC.LEVELS = {
  recruit:     {label:'Recruit', ages:'8–10', blurb:'Step-by-step math. No clock to beat.', manual:2, showMath:true, clock:false},
  codebreaker: {label:'Codebreaker', ages:'11–13', blurb:'The math shows after a wrong try. The clock is on.', manual:3, showMath:false, clock:true},
  expert:      {label:'Cryptanalyst', ages:'14+', blurb:'Every group by hand. A tighter clock.', manual:99, showMath:false, clock:true, tight:true},
};
SC.LEVEL_ORDER = ['recruit', 'codebreaker', 'expert'];

SC.MENTOR = {name:'Lt. Jack Marlow', title:'Your mentor at Station HYPO', avatar:32,
  note:'Lieutenant Marlow is made up for the game. The real people of Station HYPO appear on the history cards.'};

/* Words the US codebreakers had already worked out before the campaign starts. */
SC.BASE_WORDS = ['FROM', 'FIRST FLEET', 'FOURTH FLEET', 'SUPPLY OFFICE', 'WEATHER REPORT', 'CLEAR SKIES', 'RAIN', 'FOG', 'STRONG WIND',
  'CLOUDY', 'TANKER', 'ARRIVES', 'SAILS', 'TODAY', 'TOMORROW', 'FUEL', 'NEEDED', 'AT', 'FOR', 'ON', 'OF', 'IS', 'AND', 'SUBMARINE',
  'SUPPLY SHIPS', 'LEAVE', 'CONVOY', 'TRANSPORTS', 'INVASION FORCE', 'STRIKE FORCE', 'CARRIERS', 'ATTACK', 'ATTACKS', 'AIRFIELD', 'CAPTURE',
  'OCCUPATION FORCE', 'OPERATION', 'MO', 'AF', 'SHORT', 'WATER', 'SEND', 'SOUTH', 'APPROACH', 'WILL', 'HIDES IN', 'JUNE 4',
  'SAIPAN', 'RABAUL', 'KWAJALEIN', 'WAKE', 'KURE', 'NEW GUINEA', 'BEGINS'];
/* Words the player works out during the campaign. Once found, they stay in the codebook for later missions. */
SC.TARGET_WORDS = ['TRUK', 'PORT MORESBY', 'NORTHWEST'];
SC.ALL_WORDS = SC.BASE_WORDS.concat(SC.TARGET_WORDS, ['PEARL HARBOR', 'TOKYO', 'HAWAII', 'EAST', 'SOUTHEAST']);

/* Everyday enemy messages ("filler") built from these patterns: real codebreakers read thousands like them. */
SC.FILLER = {
  bases: ['SAIPAN', 'RABAUL', 'KWAJALEIN', 'WAKE', 'KURE'],
  weather: ['CLEAR SKIES', 'RAIN', 'FOG', 'STRONG WIND', 'CLOUDY'],
  senders: ['FIRST FLEET', 'FOURTH FLEET', 'SUPPLY OFFICE'],
  day: ['TODAY', 'TOMORROW'],
  patterns: [
    ['FROM', '$sender', 'WEATHER REPORT', '$base', '$weather'],
    ['FROM', '$sender', 'TANKER', 'ARRIVES', '$base', '$day'],
    ['FROM', '$sender', 'SUPPLY SHIPS', 'LEAVE', '$base', '$day'],
    ['FROM', '$sender', 'FUEL', 'NEEDED', 'AT', '$base'],
    ['FROM', '$sender', 'SUBMARINE', 'ARRIVES', '$base', '$day'],
    ['FROM', '$sender', 'CONVOY', 'SAILS', 'FROM', '$base', '$day'],
  ],
};

/* Places on the campaign map (longitude east of Greenwich, so Hawaii is past 180). */
SC.PLACES = {
  tokyo:[139.7, 35.7, 'Tokyo'], kure:[132.6, 34.2, 'Kure'], truk:[151.8, 7.4, 'Truk'], saipan:[145.7, 15.2, 'Saipan'], rabaul:[152.2, -4.2, 'Rabaul'],
  moresby:[147.2, -9.5, 'Port Moresby'], wake:[166.6, 19.3, 'Wake'], kwaj:[167.7, 9.2, 'Kwajalein'], midway:[182.6, 28.2, 'Midway'],
  pearl:[202.0, 21.3, 'Pearl Harbor'], aleut:[187, 52.5, 'Aleutian Islands'], luck:[186.5, 32.2, 'Point Luck'],
};

SC.CAMPAIGNS = [{
  id:'midway', title:'The Midway Code', sub:'Pacific, 1942', side:'us', office:'Station HYPO, Pearl Harbor',
  blurb:'Six months after Pearl Harbor, a small team in a basement is trying to read the Japanese Navy\'s main code. You join them.',
  missions:[
  {
    id:'m1', title:'The Dungeon', date:'March 1942', place:'Station HYPO, Pearl Harbor', pin:'pearl', clockStart:'1942-03-02T08:00', rate:4,
    goal:'Read your first two enemy messages and find out where the tanker is going.',
    briefing:['Welcome to Station HYPO, cadet. We work in a basement with no windows. Everyone calls it the Dungeon.',
      'The Japanese Navy hides its messages with a code we call JN-25. Every word is a 5-digit number, and then a second number is added on top to hide it.',
      'Today you learn the trick: take the extra number away, and look the word up in our codebook.'],
    tutorial:true, limit:{codebreaker:0, expert:0},
    phases:[
      {k:'decode', keys:['k1', 'k2'], filler:0, say:'Decode both messages. Start with the one on top.'},
      {k:'vote', id:'where', q:'Where is the tanker going?', opts:[
        {t:'Truk', ok:true, why:'Yes. Truk is a big Japanese base in the middle of the Pacific, so fuel ships go there.'},
        {t:'Pearl Harbor', why:'Pearl Harbor is our base. A Japanese tanker would never sail into it.'},
        {t:'Tokyo', why:'Look again at the decoded message: the tanker arrives at the place you just worked out.'}]},
    ],
    messages:{
      k1:{words:['FROM', 'FOURTH FLEET', 'WEATHER REPORT', 'TRUK', 'CLEAR SKIES'], plain:'A weather report from a place we cannot read yet.'},
      k2:{words:['FROM', 'SUPPLY OFFICE', 'TANKER', 'ARRIVES', 'TRUK', 'TOMORROW'], plain:'A fuel ship arrives tomorrow at the same unknown place.',
        fact:'A Japanese tanker arrives at Truk tomorrow.'},
    },
    targets:{TRUK:{opts:['TRUK', 'PEARL HARBOR', 'RAIN'],
      clue:'This group sits where a place name goes. Ships deliver fuel there, and the Japanese Navy sends weather reports from there.',
      why:{'PEARL HARBOR':'Pearl Harbor is our own base. The enemy would not report its weather or send tankers there.', RAIN:'Rain is weather, not a place. "Tanker arrives rain" makes no sense.'}}},
    news:[{at:20, icon:'radio', t:'Station HYPO works around the clock'}, {at:70, icon:'ship', t:'Navy asks: where will Japan strike next?'},
      {on:'win', icon:'pin', t:'Tanker route to Truk added to the plot board'}],
    outcome:{win:['Tanker route confirmed: Truk.', 'Well done, cadet. Every message you read fills in the picture.']},
    history:{title:'The Dungeon at Pearl Harbor', person:'hypo', lines:[
      'Station HYPO was the US Navy codebreaking unit at Pearl Harbor, working in a windowless basement.',
      'Its people worked shifts of 20 hours or more after the attack on Pearl Harbor in December 1941.',
      'They used IBM punch-card machines to help with the endless sums, just like the strip machine in the game.'],
      simplified:'Real JN-25 messages were longer, and the additive book was secret too: codebreakers had to work out the additives themselves. In the game you get the additives for free.'},
  },
  {
    id:'m2', title:'Operation MO', date:'April 1942', place:'Coral Sea', pin:'moresby', clockStart:'1942-04-20T06:00', rate:6,
    goal:'Find out where Operation MO, a big Japanese invasion, is aimed.',
    briefing:['The Japanese messages keep mentioning an operation called MO. Transports are gathering at Rabaul.',
      'If we know the target, our carriers can get there first. Decode the messages and find the place.'],
    limit:{codebreaker:420, expert:300},
    phases:[
      {k:'decode', keys:['k1', 'k2', 'k3'], filler:1, say:'Decode the messages about Operation MO. One place name is not in our codebook yet.'},
      {k:'vote', id:'target', q:'Where is Operation MO aimed?', opts:[
        {t:'Port Moresby, New Guinea', ok:true, why:'Right. Port Moresby is close to Rabaul, and its airfield would let Japan threaten Australia.'},
        {t:'Hawaii', why:'Hawaii is thousands of miles from Rabaul. The messages say the invasion force sails from Rabaul.'},
        {t:'Tokyo', why:'Tokyo is the capital of Japan. Japan would not invade its own capital.'}]},
    ],
    messages:{
      k1:{words:['OPERATION', 'MO', 'INVASION FORCE', 'SAILS', 'FROM', 'RABAUL'], plain:'The invasion force for Operation MO sails from Rabaul.', fact:'Operation MO: the invasion force sails from Rabaul.'},
      k2:{words:['TRANSPORTS', 'FOR', 'PORT MORESBY', 'LEAVE', 'RABAUL', 'TOMORROW'], plain:'Transports leave Rabaul for an unknown place tomorrow.'},
      k3:{words:['CAPTURE', 'PORT MORESBY', 'AIRFIELD', 'NEW GUINEA'], plain:'They want to capture an airfield on New Guinea.', fact:'The target has an airfield on New Guinea.'},
    },
    targets:{'PORT MORESBY':{opts:['PORT MORESBY', 'HAWAII', 'TOKYO'],
      clue:'Transports leave Rabaul for this place, and it has an airfield on New Guinea. Look at the map: what is close to Rabaul?',
      why:{HAWAII:'Hawaii is not on New Guinea, and it is very far from Rabaul.', TOKYO:'Tokyo is in Japan, not New Guinea.'}}},
    news:[{at:30, icon:'ship', t:'Japanese ships gather at Rabaul'}, {at:120, icon:'plane', t:'Reports of carriers moving south'},
      {at:240, icon:'radio', t:'Invasion force expected to sail soon'}, {at:330, icon:'ship', t:'Transports leaving Rabaul'},
      {on:'win', icon:'ship', t:'US carriers race to the Coral Sea'}, {on:'late', icon:'ship', t:'Our carriers sail late for the Coral Sea'}],
    outcome:{win:['US carriers Lexington and Yorktown are sent to the Coral Sea.', 'They will meet the invasion force before it reaches Port Moresby.'],
      late:['The report came late, but other codebreakers had pieces of it too.', 'US carriers still reached the Coral Sea in time.']},
    history:{title:'The Battle of the Coral Sea', person:'driscoll', lines:[
      'US codebreakers at Pearl Harbor, Melbourne and Washington worked out that Operation MO was aimed at Port Moresby.',
      'From May 4 to 8, 1942, US and Japanese carriers fought the first sea battle in which the ships never saw each other: only their planes did.',
      'The US carrier Lexington was sunk and many sailors and airmen on both sides were killed.',
      'The invasion of Port Moresby was called off.'],
      simplified:'The real target code was a short designator, not the full name, and it took several codebreaking teams together.'},
  },
  {
    id:'m3', title:'AF Is Short of Water', date:'May 1942', place:'Pearl Harbor and Midway', pin:'midway', clockStart:'1942-05-14T09:00', rate:6,
    goal:'Prove which place the code letters AF stand for.',
    briefing:['Japan is planning its biggest attack yet. The messages name the target only as AF.',
      'We think AF is Midway, a small island base. Washington thinks it could be Hawaii, or the Aleutian Islands near Alaska.',
      'Guessing is not good enough. We need proof.'],
    limit:{codebreaker:540, expert:400},
    phases:[
      {k:'decode', keys:['k1', 'k2'], filler:1, say:'Decode the messages about AF.'},
      {k:'vote', id:'prove', q:'How can we prove what AF means?', opts:[
        {t:'Set a trap: have Midway send a fake message that the enemy will report', ok:true, why:'Yes! If the enemy repeats our fake news and calls the place AF, we have our proof.'},
        {t:'Ask Washington to decide', why:'Washington has the same messages we do. Asking again will not give anyone proof.'},
        {t:'Wait and see where they attack', why:'By then it would be too late to get our carriers in position.'}]},
      {k:'vote', id:'channel', q:'How do we tell Midway about the trap?', opts:[
        {t:'By the undersea telegraph cable', ok:true, why:'Right. The cable runs along the sea floor, so the enemy cannot listen in.'},
        {t:'By radio, in our own code', why:'Risky. Radio can be heard by anyone. If the enemy ever read it, the trap would be spoiled.'},
        {t:'By radio, in plain English', why:'The enemy would hear the whole plan. That is the opposite of a trap!'}]},
      {k:'vote', id:'fake', q:'What should Midway send by radio?', opts:[
        {t:'"Our water machine broke. We are short of fresh water." In plain English.', ok:true, why:'Perfect. Plain English is easy for the enemy to hear, and a water problem sounds real and not too important.'},
        {t:'The same message, but in our secret code', why:'The enemy might not be able to read our code, and then they would never report it.'},
        {t:'"This is a trap, please report it."', why:'Ha! Then the enemy would know it is a trap and say nothing.'}]},
      {k:'decode', keys:['k3'], filler:1, say:'Midway sent the fake message. Now listen: an enemy message has just been picked up.'},
      {k:'vote', id:'af', q:'What is AF?', opts:[
        {t:'Midway', ok:true, why:'Proved! The enemy reported that AF is short of water, and only Midway sent that message.'},
        {t:'Hawaii', why:'Hawaii never said it was short of water. Only Midway did.'},
        {t:'The Aleutian Islands', why:'The Aleutians never sent a water message. Only Midway did.'}]},
    ],
    messages:{
      k1:{words:['STRIKE FORCE', 'CARRIERS', 'WILL', 'ATTACK', 'AF'], plain:'The carrier strike force will attack AF.', fact:'A carrier strike force will attack AF.'},
      k2:{words:['OCCUPATION FORCE', 'SAILS', 'FOR', 'AF', 'FROM', 'SAIPAN'], plain:'Troops sail from Saipan to take over AF.', fact:'Troops will land on AF.'},
      k3:{words:['FROM', 'FOURTH FLEET', 'AF', 'IS', 'SHORT', 'OF', 'WATER'], plain:'The enemy reports: AF is short of water!', fact:'Enemy report: "AF is short of water."'},
    },
    news:[{at:40, icon:'radio', t:'Enemy radio traffic is growing fast'}, {at:150, icon:'map', t:'Navy debates: is the target Midway or Hawaii?'},
      {at:300, icon:'ship', t:'Japanese fleet getting ready to sail'}, {at:450, icon:'ship', t:'Time is running out to place our carriers'},
      {on:'phase:4', icon:'radio', t:'Midway radios: water machine broken'},
      {on:'win', icon:'pin', t:'Admiral Nimitz: target is Midway'}, {on:'late', icon:'pin', t:'Proof arrives at the last minute'}],
    outcome:{win:['AF is Midway. Admiral Nimitz now trusts the codebreakers.', 'He starts moving every carrier he has towards Midway.'],
      late:['The proof arrived late, but it arrived.', 'Admiral Nimitz decides to defend Midway.']},
    history:{title:'The water trick', person:'rochefort', lines:[
      'In May 1942 the HYPO team believed AF was Midway, but some officers in Washington disagreed.',
      'Midway was told by undersea cable to send a plain-language radio message saying its water plant had broken down.',
      'Soon a Japanese message was read saying that AF was short of water.',
      'The idea is usually credited to Jasper Holmes, working with Joseph Rochefort.'],
      simplified:'The real messages were longer and took days to read. The three decisions are made up for the game, but the plan really worked this way.'},
  },
  {
    id:'m4', title:'The Battle of Midway', date:'June 1942', place:'North of Midway', pin:'luck', clockStart:'1942-05-27T07:00', rate:8,
    goal:'Find out when the attack comes and from which direction, so our carriers can wait in the right place.',
    briefing:['We know the target is Midway. Now we need two more answers: when, and from which direction?',
      'Our three carriers must be waiting in the right place at the right time. Every message counts.'],
    limit:{codebreaker:540, expert:400},
    phases:[
      {k:'decode', keys:['k1', 'k2', 'k3', 'k4'], filler:2, say:'Decode the attack plans. One direction word is not in our codebook yet.'},
      {k:'vote', id:'when', q:'When will the attack on Midway begin?', opts:[
        {t:'June 4', ok:true, why:'Yes. The date table that Joseph Finnegan and Wesley Wright worked out gives June 4.'},
        {t:'June 10', why:'Check the decoded strike message again: the date is in it.'},
        {t:'July 4', why:'Check the decoded strike message again: the date is in it.'}]},
      {k:'vote', id:'where', q:'Where should our carriers wait?', opts:[
        {t:'Northeast of Midway, out of sight, ready to strike the enemy carriers from the side', ok:true, why:'Right. The enemy comes from the northwest, so waiting to the northeast lets our planes hit them by surprise.'},
        {t:'Right next to Midway', why:'Enemy planes attacking Midway would spot our carriers at once.'},
        {t:'Back at Pearl Harbor', why:'Pearl Harbor is over 1,000 miles away. Our planes could never reach the fight.'}]},
    ],
    messages:{
      k1:{words:['STRIKE FORCE', 'ATTACKS', 'AF', 'ON', 'JUNE 4'], plain:'The carrier strike force attacks Midway on June 4.', fact:'The attack on Midway begins June 4.'},
      k2:{words:['CARRIERS', 'APPROACH', 'AF', 'FROM', 'NORTHWEST'], plain:'Their carriers come from an unknown direction.', fact:'Enemy carriers will come from the northwest.'},
      k3:{words:['WEATHER REPORT', 'NORTHWEST', 'OF', 'AF', 'FOG', 'AND', 'RAIN'], plain:'Fog and rain in an unknown direction from Midway.'},
      k4:{words:['STRIKE FORCE', 'HIDES IN', 'FOG'], plain:'Their strike force will hide in the fog.', fact:'The strike force will hide in the fog.'},
    },
    targets:{NORTHWEST:{opts:['NORTHWEST', 'EAST', 'SOUTHEAST'],
      clue:'The carriers approach from this direction. The weather there is fog and rain, and the strike force hides in fog. Japan is to the west of Midway.',
      why:{EAST:'East of Midway is the way to Hawaii, our side. And Japan is to the west.', SOUTHEAST:'Southeast of Midway is towards Hawaii, our side. And Japan is to the west.'}}},
    news:[{at:30, icon:'ship', t:'Japanese fleet leaves home waters'}, {at:120, icon:'ship', t:'US carriers refuel at Pearl Harbor'},
      {at:220, icon:'plane', t:'Patrol planes search the ocean west of Midway'}, {at:330, icon:'ship', t:'Yorktown repaired in record time'},
      {at:430, icon:'radio', t:'Enemy fleet getting close'},
      {on:'win', icon:'ship', t:'US carriers waiting northeast of Midway'}, {on:'late', icon:'ship', t:'Our carriers rush into position'}],
    outcome:{win:['Our carriers wait northeast of Midway, at a spot called Point Luck.', 'On June 4, their planes find the enemy carriers first.'],
      late:['The report came late. Our carriers had to rush.', 'Even so, on June 4 their planes found the enemy carriers.']},
    history:{title:'The Battle of Midway', person:'finnegan', lines:[
      'Thanks to the codebreakers, three US carriers were waiting northeast of Midway on June 4, 1942.',
      'In the battle, Japan lost four aircraft carriers. The US lost the carrier Yorktown.',
      'About 3,000 Japanese and over 300 Americans were killed.',
      'Midway is often called the turning point of the war in the Pacific.'],
      simplified:'The game shows only a few of the many messages that were read. The direction word in the game stands for many clues the real codebreakers put together.'},
  },
  ],
}];

/* Real people, for the history cards and the Records Room. Check every fact against a reliable source before release. */
SC.PEOPLE = {
  hypo:{name:'The Station HYPO team', years:'1941–1945', role:'US Navy codebreakers at Pearl Harbor',
    lines:['A small team of codebreakers, language officers and machine operators, including the band of the battleship California, whose ship was sunk at Pearl Harbor.',
      'Many kept their work secret for decades after the war.']},
  driscoll:{name:'Agnes Meyer Driscoll', years:'1889–1971', role:'US Navy codebreaker',
    lines:['One of the Navy\'s greatest codebreakers, she broke many Japanese codes between the wars.',
      'Her early work on JN-25 in 1940 helped the codebreakers of 1942.']},
  rochefort:{name:'Joseph Rochefort', years:'1900–1976', role:'Commander of Station HYPO',
    lines:['He led the codebreakers at Pearl Harbor and trusted their reading that AF was Midway.',
      'His work stayed secret for many years. He was awarded the Distinguished Service Medal in 1986, ten years after he died.']},
  finnegan:{name:'Joseph Finnegan and Wesley Wright', years:'', role:'Codebreakers at Station HYPO',
    lines:['Just before the battle they cracked the separate code the Japanese used for dates.',
      'It showed the attack on Midway would come on June 4.']},
};

/* The mentor's lines on the workstation, short and friendly. */
SC.SAY = {
  stripFirst:'Subtract the additive from the message group, one digit at a time.',
  stripMore:'Next group. Same trick: take the additive away.',
  machine:'You have the hang of it. The strip machine can do the rest of this message.',
  lookup:'Now look the number up in the codebook.',
  unknown:'This group is not in our codebook yet. Tap it and work out what it means.',
  read:'Message read! File it on the board.',
  allFiled:'All the messages for this step are read.',
  vote:'Time to decide. Pick the best answer.',
  teamVote:'Everyone votes. The team goes with the most popular answer.',
  wait:'Waiting for the rest of the team…',
  notDiv3:'That is not a real code group: its digits do not add up to a number that divides by 3. One digit is off.',
  noMatch:'That number divides by 3, but it is not in the codebook. One digit must still be off.',
  wrongTarget:'Not quite.',
  goodDigit:['Nice.', 'Good.', 'Yes.', 'Right.'],
  welcomeBack:'Welcome back, cadet.',
};

/* Stamps and wording for the news teletype. */
SC.NEWS_ICON = {ship:'⚓', plane:'✈', radio:'📻', map:'🗺', pin:'📍'};
})();
