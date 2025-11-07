// Quick script to get your user ID from the database
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function getUserId() {
  try {
    // Get all users
    const users = await prisma.user.findMany({
      select: {
        id: true,
        email: true,
        name: true,
      },
      take: 10
    });

    console.log('\n📋 Users in database:\n');
    users.forEach((user, index) => {
      console.log(`${index + 1}. ${user.name || 'No name'} (${user.email || 'No email'})`);
      console.log(`   User ID: ${user.id}\n`);
    });

    if (users.length === 0) {
      console.log('❌ No users found in database');
      console.log('   You may need to sign up/login first to create a user');
    } else if (users.length === 1) {
      console.log(`✅ Using User ID: ${users[0].id}`);
    }
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await prisma.$disconnect();
  }
}

getUserId();

