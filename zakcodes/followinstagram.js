// Define a function to find and click the Follow button
function follow() {
    // Find the Follow button based on its class names and inner text
    const followButton = document.querySelector('div._ap3a._aaco._aacw._aad6._aade');
    
    // Check if the button's inner text is "Follow"
    if (followButton && followButton.innerText.toLowerCase() === 'follow') {
        followButton.click();
        console.log('Follow button clicked!');
    } else {
        console.log('Follow button not found.');
    }
}

// Execute the function
follow();