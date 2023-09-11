$(document).ready(function() {
    
    // Start the ticker, we count down every second regardless
	setInterval(function() {
	  $('.countdown').each(function () {
	     if (!$(this).data('playing'))
	       return;
	     
		 var c = $(this).text() - 0;
		 var voting_valid = false
		 if (c > 0) {
            $(this).text(c - 1);
			voting_valid = true;
		 }

		 // Only use the value of voting_valid if we are on the relevant id
		 if ($(this).attr('id') == 'vote-remaining') {
			$('#voting-container').toggle(!!voting_valid);
			$('#no-voting-container').toggle(!voting_valid);
		 }
	  })
	}, 1000);
    
    
    
    
	var socket = io();
    
	socket.on('connect', function() {
		console.log("connected");
		$('#status-connected').show();
		$('#status-not-connected').hide();
    });
	
	socket.on('disconnect', function() {
		console.log("disconnected");
		$('#status-connected').hide();
		$('#status-not-connected').show();
    });
	
	
	socket.on('now-playing', function(msg) {
		console.log('Now playing: ', msg)
		
		$('#now-playing-artist').text(msg.artist);
		$('#now-playing-title').text(msg.title);
		$('#now-playing-image').attr('src', msg.image_url);
		
		$('#now-playing-remaining').text(Math.round(msg.track_remaining / 1000)).data("playing", msg.is_playing);
		$('#vote-remaining').text(Math.round(msg.voting_remaining / 1000)).data("playing", msg.is_playing);
		
		$('#playlist').attr('href', msg.playlist.uri).text(msg.playlist.name)
		$('.playlist').toggle(!!msg.playlist.name)
		
		$('#playing-container').toggle(!!msg.is_playing);
		$('#nothing-playing-container').toggle(!msg.is_playing);
		
		if (!msg.is_playing) {
			$('#voting-container').hide();
			$('#no-voting-container').hide();
		}
		
		
	});
	
	socket.on('vote', function(votes) {
		console.log('Votes: ', votes)
		$('#skip-votes').text(votes.skip)
		$('#keep-votes').text(votes.keep)
		
		bar_size = 20;
		votes.skip = votes.skip + 0.5 // Adding some numbers to make the bar look better
		votes.keep = votes.keep + 0.5
		total = votes.skip + votes.keep
		percent = (votes.keep / total) * 100
		ignoring_bar_size = percent - (bar_size / 2)
		$('#voting-progress').width(bar_size + '%').css('margin-left', ignoring_bar_size + '%');
	});
	
	$('.vote').on('click', function (e) {
		console.log(e.target.id + ' voted')
		$(e.target).prop('disabled', true).fadeTo(200, .10).delay(2000).queue(function (n) { $(this).prop('disabled', false).fadeTo(200, 1); n(); });
		socket.emit('vote', {'for': e.target.id});
	});
});

